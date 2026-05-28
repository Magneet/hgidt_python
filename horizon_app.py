from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import horizon_functions


def build_pod_info(hvconnectionobj, config_server_name):
    """Discover pods and connection servers from an active Horizon connection.

    Returns (pods, connection_servers) without mutating any globals.
    """
    federation = horizon_functions.Federation(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    config = horizon_functions.Config(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)
    monitor = horizon_functions.Monitor(
        url=hvconnectionobj.url, access_token=hvconnectionobj.access_token)

    cpa_status = federation.get_cloud_pod_federation()['connection_server_statuses'][0]['status']
    pods = []
    connection_servers = []

    if cpa_status == "ENABLED":
        for pod in federation.get_pods():
            pod_name = pod['name']
            pods.append(pod_name)
            for endpoint in federation.get_pod_endpoints(pod_id=pod['id']):
                dns = (endpoint['server_address'].replace("https://", "")).split(":")[0]
                connection_servers.append({
                    'PodName': pod_name,
                    'Name': dns.split(".")[0],
                    'ServerDNS': dns,
                })
    else:
        env_details = config.get_environment_properties()
        connection_servers_details = monitor.connection_servers()
        pod_name = env_details['cluster_name']
        pods.append(pod_name)
        for conserver in connection_servers_details:
            conserver_name = conserver['name']
            if len(conserver_name.split(".")) > 1:
                dns = conserver_name
            else:
                dns_domain = config_server_name.replace(
                    config_server_name.split(".")[0], "")
                dns = conserver_name + dns_domain
            connection_servers.append({
                'PodName': pod_name,
                'Name': conserver_name,
                'ServerDNS': dns,
            })

    return pods, connection_servers


def connect_to_pod(pod, connection_servers, username, domain, password):
    """Connect to any available connection server in *pod*.

    Returns (hvconnectionobj, server_dns) on success, (False, None) on failure.
    """
    for con_server in (s for s in connection_servers if s["PodName"] == pod):
        server_dns = con_server['ServerDNS']
        logger.info("connecting to: " + server_dns)
        conn = horizon_functions.Connection(
            username=username, domain=domain, password=password,
            url="https://" + server_dns)
        try:
            conn.hv_connect()
            logger.info("Connected to: " + server_dns)
            return conn, server_dns
        except Exception as e:
            logger.error("Failed to connect to: " + server_dns)
            logger.error(str(e))

    return False, None


def _fetch_vm_snapshots(args):
    """Fetch snapshots for a single base VM; designed for ThreadPoolExecutor.map."""
    basevm, external, vcenter_id = args
    try:
        snaps = external.get_base_snapshots(vcenter_id=vcenter_id, base_vm_id=basevm['id'])
    except Exception as e:
        logger.error(f"Failed to get snapshots for VM {basevm['id']}: {e}")
        snaps = []
    if not isinstance(snaps, list):
        snaps = [snaps]
    basevm['snapshotcount'] = len(snaps)
    for snap in snaps:
        snap['basevmid'] = basevm['id']
    return basevm, snaps


def load_environment_data(pods, connection_servers, username, domain, password, on_status=None, include_vms_snapshots=True):
    """Load all Horizon environment data needed by the UI.

    Returns a dict with keys: desktop_pools, rds_farms, base_vms,
    base_snapshots, datacenters, vcenters, include_vms_snapshots.
    on_status(message) is called with progress strings when provided.
    When include_vms_snapshots is False, only pools and farms are fetched.
    """
    desktop_pools = []
    rds_farms = []
    base_vms = []
    base_snapshots = []
    datacenters = []
    vcenters = []

    vdi_filter = {
        "type": "And",
        "filters": [
            {"type": "Equals", "name": "source", "value": "INSTANT_CLONE"},
            {"type": "Equals", "name": "type", "value": "AUTOMATED"},
        ],
    }
    rds_filter = {
        "type": "Equals",
        "name": "automated_farm_settings.image_source",
        "value": "VIRTUAL_CENTER",
    }

    for pod in pods:
        logger.info(f'Connecting to Pod: {pod}')
        if on_status:
            on_status(f"Connecting to pod: {pod}")
        hvconn, _ = connect_to_pod(pod, connection_servers, username, domain, password)
        if hvconn is False:
            logger.error(f"Could not connect to any server in pod: {pod}")
            continue

        try:
            inventory = horizon_functions.Inventory(
                url=hvconn.url, access_token=hvconn.access_token)
            config = horizon_functions.Config(
                url=hvconn.url, access_token=hvconn.access_token)
            external = horizon_functions.External(
                url=hvconn.url, access_token=hvconn.access_token)

            logger.info(f'Getting Desktop Pools')
            for pool in inventory.get_desktop_pools(filter=vdi_filter):
                pool['pod'] = pod
                logger.info(f'Found Pool: {pool["name"]}')
                desktop_pools.append(pool)

            logger.info(f'Getting RDS Farms')
            for farm in inventory.get_farms(filter=rds_filter):
                farm['pod'] = pod
                logger.info(f'Found Farm: {farm["name"]}')
                rds_farms.append(farm)

            if include_vms_snapshots:
                logger.info("Getting vCenters")
                pod_vcenters = config.get_virtual_centers()
                for vcenter in pod_vcenters:
                    vcenter['pod'] = pod
                    logger.info(f'Found vCenter: {vcenter["server_name"]}')

                    pod_datacenters = external.get_datacenters(vcenter_id=vcenter['id'])
                    for datacenter in pod_datacenters:
                        datacenter['pod'] = pod
                        logger.info(f'Found Datacenter {datacenter["name"]}')

                        raw_vms = external.get_base_vms(
                            vcenter_id=vcenter['id'],
                            datacenter_id=datacenter['id'],
                            filter_incompatible_vms=True)
                        if not isinstance(raw_vms, list):
                            raw_vms = [raw_vms]
                        for vm in raw_vms:
                            if 'incompatible_reasons' not in vm:
                                vm['incompatible_reasons'] = []
                            vm['pod'] = pod

                        logger.info(f"Fetching snapshots for {len(raw_vms)} VMs in parallel")
                        if on_status:
                            on_status(f"Fetching snapshots for {len(raw_vms)} VMs in {datacenter['name']}")

                        args = [(vm, external, vcenter['id']) for vm in raw_vms]
                        with ThreadPoolExecutor(max_workers=5) as executor:
                            results = list(executor.map(_fetch_vm_snapshots, args))

                        for vm, snaps in results:
                            if snaps:
                                base_snapshots.extend(snaps)
                        base_vms.extend(raw_vms)
                        logger.info("Done getting Base VMs and snapshots")

                    datacenters.extend(pod_datacenters)
                vcenters.extend(pod_vcenters)
            else:
                logger.info("Skipping Golden Images & Snapshots refresh (disabled in config)")

        finally:
            logger.info(f'Disconnecting from Pod: {pod}')
            hvconn.hv_disconnect()

    return {
        'desktop_pools': desktop_pools,
        'rds_farms': rds_farms,
        'base_vms': base_vms,
        'base_snapshots': base_snapshots,
        'datacenters': datacenters,
        'vcenters': vcenters,
        'include_vms_snapshots': include_vms_snapshots,
    }
