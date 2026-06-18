# Horizon Golden Image Deployment Tool (HGIDT)

A desktop application for managing VMware Horizon instant-clone desktop pools and RDS farms. Push new golden images, manage provisioning, resize compute profiles, and schedule deployments — all without touching the Horizon Admin console.

---

## Features

- Push a new base VM and snapshot to instant-clone VDI desktop pools and RDS farms
- Pre-selects the currently configured golden image and snapshot when a pool/farm is selected
- Enable or disable provisioning per pool/farm
- Schedule image pushes for a specific date and time
- Resize compute profile (CPU count, cores per socket, RAM) as part of a push
- Secondary image support (stage an image without immediately promoting it)
- Multi-pod (CPA federation) support, with an optional "Local Pod Only" mode
- Credentials stored securely in the OS keychain

---

## Requirements

- VMware Horizon 2312 or later (REST API must be reachable from the machine running the tool)
- An account with sufficient Horizon admin privileges to update desktop pools and farms

---

## Using the Tool

### 1. Configuration tab

| Field | Description |
|---|---|
| Connection Server | Hostname or FQDN of a Horizon Connection Server |
| Username | Horizon admin username (without domain) |
| Domain | Active Directory domain |
| Set Password | Opens a dialog to enter your password |
| Save Password | Saves the password in the OS keychain for future sessions |
| Log Level | Controls log verbosity (`INFO` is recommended for normal use) |
| Refresh Golden Images & Snapshots | When enabled, the Connect/Refresh button also reloads the base VM and snapshot lists. Disable this for faster refreshes when you only need to update pool settings |
| Local Pod Only | Skip CPA federation discovery and work with the local Horizon pod only. Useful when federation is not configured or the CPA API is unavailable |
| VM Name Filter | Comma-separated list of partial VM name matches (case-insensitive). When set, snapshot data is only fetched for VMs whose names contain at least one of the terms (e.g. `win11-gold, server2022`). All VMs still appear in the VM picker; this filter only limits which ones have their snapshots loaded, which speeds up the initial connect when there are many VMs in vCenter. Leave empty to fetch snapshots for all VMs |

After filling in the fields:
1. Click **Set Password** and enter your password.
2. Click **Save Configuration**.
3. Optionally click **Test Credentials** to verify the connection before switching tabs.

---

### 2. VDI Desktop Pools tab

1. Click **Connect** to authenticate and load instant-clone VDI pools and golden images.  
   The button changes to **Refresh** once connected — click it again to reload data.
2. Select a **Desktop Pool** from the dropdown. The current base VM and snapshot configured for that pool are pre-selected automatically.
3. Optionally pick a different **Golden Image** (base VM) and **Snapshot**.
4. Configure additional options if needed:
   - **Log-off Policy** — whether to force-log off sessions or wait
   - **Resize** — override CPU count, cores per socket, and RAM for the push
   - **Scheduled push** — enable a date/time picker to delay the push
   - **Secondary Image** — stage the image without immediately promoting it, and optionally limit how many machines receive it first
5. Click **Apply Golden Image** to push.
6. Use **Enable Provisioning / Disable Provisioning** to toggle the pool's provisioning state independently of an image push.

---

### 3. RDS Farms tab

Works the same as the VDI tab but targets automated instant-clone RDS farms.

---

### Changing the connection server

If you update the Connection Server address on the Configuration tab and save, the tool automatically resets to the disconnected state so you reconnect to the new server cleanly.

---

## Running from source

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows PowerShell

pip install -r requirements.txt

python horizon_golden_image_deployment_tool.py
```

---

## Building a distributable

### Windows

**Prerequisites:** Python 3.11+, PowerShell 5.1 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
.\build_pyinstaller.ps1
```

Outputs:

| Path | Description |
|---|---|
| `dist\Horizon Golden Image Deployment Tool\` | Standalone folder — copy this anywhere and run `Horizon Golden Image Deployment Tool.exe` directly, no installation or ZIP required |
| `installer\Horizon_Golden_Image_Deployment_Tool_v1.0.0_Windows.zip` | ZIP of the above folder, ready to distribute |

---

### macOS

**Prerequisites:** Python 3.11+, Xcode Command Line Tools (`xcode-select --install`).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x build_mac.sh
./build_mac.sh
```

Outputs:

| Path | Description |
|---|---|
| `dist/Horizon Golden Image Deployment Tool.app` | Standalone `.app` bundle — drag it to `/Applications` or double-click it directly, no DMG required |
| `installer/Horizon_Golden_Image_Deployment_Tool_v1.0.0_macOS.dmg` | DMG ready to distribute |

> **Note:** Because the app is not signed with an Apple Developer certificate, macOS will show a Gatekeeper warning on first launch. Right-click the `.app` and choose **Open**, then confirm the prompt.

---

### Linux

**Prerequisites:** Python 3.11+, a running display server (X11 or Wayland), and the Qt XCB platform plugin dependencies (`libxcb`, `libxkbcommon`, etc. — usually already present on a desktop system).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x build_linux.sh
./build_linux.sh
```

Outputs:

| Path | Description |
|---|---|
| `dist/Horizon Golden Image Deployment Tool/` | Standalone folder — copy it anywhere and run `Horizon Golden Image Deployment Tool` directly |
| `installer/Horizon_Golden_Image_Deployment_Tool_v1.0.0_Linux.zip` | ZIP of the above folder, ready to distribute |

> **Note:** The tool stores passwords via the `keyring` library, which requires a running keyring daemon (GNOME Keyring or KWallet). On systems without one the password-save feature is silently skipped — the app still works, you will just need to re-enter your password each session.

---

## Log file

The tool writes a rotating log to `hgidt.log` in the same directory as the executable (or the working directory when running from source). The log level can be changed on the Configuration tab without restarting.
