"""
Pengambilan data kerentanan (CVE) dari NVD (National Vulnerability
Database) REST API v2.0. Berbeda dari sumber RSS lainnya, modul ini
melakukan query terstruktur berdasarkan rentang tanggal publikasi dan
skor CVSS minimum.
"""
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pandas as pd
import requests

from src.utils.http_client import buat_session_retry
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _ekstrak_skor_cvss(metrics: dict) -> Optional[float]:
    """
    Mengambil skor CVSS tertinggi yang tersedia dari objek 'metrics'
    NVD. NVD bisa punya beberapa versi CVSS sekaligus (v4, v3.1, v3.0,
    v2) tergantung kapan CVE tersebut dipublikasikan/diupdate; kita
    prioritaskan versi terbaru karena lebih akurat merefleksikan
    tingkat keparahan saat ini.
    """
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entri = metrics.get(key)
        if entri:
            return entri[0]["cvssData"]["baseScore"]
    return None


def _ekstrak_severity(metrics: dict) -> Optional[str]:
    """Mengambil label severity (LOW/MEDIUM/HIGH/CRITICAL) yang selaras dengan skor di atas."""
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30"):
        entri = metrics.get(key)
        if entri:
            return entri[0]["cvssData"].get("baseSeverity")
    entri = metrics.get("cvssMetricV2")
    if entri:
        return entri[0].get("baseSeverity")
    return None

def _ekstrak_vendor_dari_cpe(cve: dict) -> Optional[tuple]:
    """
    Mencoba ambil vendor & produk dari data CPE terstruktur. Mengembalikan
    None jika tidak tersedia — kondisi UMUM untuk CVE yang baru saja
    dipublikasikan dan belum sempat dianalisis NVD (status 'Awaiting
    Analysis'; per pertengahan 2026 mayoritas CVE baru mengalami ini).
    """
    for node_config in cve.get("configurations", []):
        for node in node_config.get("nodes", []):
            for cpe_match in node.get("cpeMatch", []):
                bagian = cpe_match.get("criteria", "").split(":")
                if len(bagian) >= 5:
                    vendor = bagian[3].replace("_", " ").title()
                    produk = bagian[4].replace("_", " ").title()
                    return vendor, produk
    return None

import re

# Aturan pemetaan pola/ekosistem plugin dan produk ke parent vendor
_ATURAN_EKOSISTEM_VENDOR = [
    # 1. WordPress Ecosystem & Plugins
    (r'\b(WordPress|WooCommerce|Elementor|Contact Form 7|Yoast|Gravity Forms|Wordfence|LiteSpeed|LearnPress|Masteriyo|Youzify|Supsystic|RegistrationMagic|Templatiq|GP Premium|Sync Post With Other Site|Cwicly|Link Library|WP Compress|Piotnet|Readabler|Ultimate Member|Divi|WPBakery|MemberPress|wpDataTables|Formidable|Smush|Rank Math|Modern Events Calendar|JetAppointment|Super Store Finder|Sticky Chat Widget|Smart Cleaning|IT Residence|Query Wrangler|User Registration & Membership Pro|Directory Pro|BookingPress|Locatoraid|Media Library Assistant|CleanTalk|Amelia|LatePoint|Bookly|WCFM|GeoDirectory|VikAppointments|Bricksforge|WP\s+[A-Za-z0-9_\-]+|All in One|NextGEN|UpdraftPlus|Slider Revolution|wpDiscuz|Brizy|Oxygen|SeedProd|Astra|GeneratePress|OceanWP|Storefront|BuddyPress|bbPress|GiveWP|Events Manager|Simple Membership|WPForms|WP-Members|Woo\s+[A-Za-z0-9_\-]+)\b', 'WordPress'),
    
    # 2. CMS, Portals & Web Frameworks
    (r'\b(Joomla|JCE|Akeeba|VirtueMart)\b', 'Joomla'),
    (r'\b(Drupal)\b', 'Drupal'),
    (r'\b(Magento|Adobe Commerce|Campaign Classic|Acrobat|Photoshop|Adobe|ColdFusion)\b', 'Adobe'),
    (r'\b(Grav|Grav CMS|Grav API)\b', 'Grav CMS'),
    (r'\b(Craft CMS)\b', 'Craft CMS'),
    (r'\b(Strapi)\b', 'Strapi'),
    (r'\b(Ghost)\b', 'Ghost'),
    (r'\b(Directus)\b', 'Directus'),
    (r'\b(Qcms)\b', 'Qcms'),
    (r'\b(siYuan|SiYuan)\b', 'siYuan'),
    (r'\b(osTicket)\b', 'osTicket'),
    (r'\b(OpenEMR)\b', 'OpenEMR'),
    (r'\b(Krayin|Krayin CRM)\b', 'Krayin'),
    (r'\b(Misskey)\b', 'Misskey'),
    (r'\b(Emlog|Emlog Pro)\b', 'Emlog'),
    (r'\b(XenForo)\b', 'XenForo'),
    (r'\b(Snipe-IT)\b', 'Snipe-IT'),
    (r'\b(Webstudio)\b', 'Webstudio'),
    (r'\b(Coolify)\b', 'Coolify'),
    (r'\b(Lara Dashboard)\b', 'Lara Dashboard'),
    (r'\b(OpenPanel)\b', 'OpenPanel'),
    (r'\b(Halo)\b', 'Halo'),
    (r'\b(Mahara)\b', 'Mahara'),
    (r'\b(Moodle)\b', 'Moodle'),
    (r'\b(Chamilo)\b', 'Chamilo'),
    (r'\b(Canvas LMS)\b', 'Canvas LMS'),
    (r'\b(StudIP|Stud\.IP)\b', 'Stud.IP'),
    (r'\b(MyBB)\b', 'MyBB'),
    (r'\b(phpBB)\b', 'phpBB'),
    (r'\b(Discourse)\b', 'Discourse'),
    (r'\b(vBulletin)\b', 'vBulletin'),
    (r'\b(Roundcube)\b', 'Roundcube'),
    (r'\b(Nextcloud)\b', 'Nextcloud'),
    (r'\b(ownCloud)\b', 'ownCloud'),
    (r'\b(OpnForm)\b', 'OpnForm'),
    (r'\b(vsDesk)\b', 'vsDesk'),
    (r'\b(SPIP)\b', 'SPIP'),
    (r'\b(EverShop)\b', 'EverShop'),
    (r'\b(Jet Admin)\b', 'Jet Admin'),

    # 3. Big Tech, Enterprise & Cloud
    (r'\b(Microsoft|Windows|Office|Exchange|Azure|SharePoint|Hyper-V|Edge|Outlook|PowerShell|Copilot|Entra|Skype|Visual Studio|Telnet Client)\b', 'Microsoft'),
    (r'\b(Google|Chrome|Chromium|Android|Pixel)\b', 'Google'),
    (r'\b(Apple|iOS|macOS|watchOS|tvOS|Safari|WebKit)\b', 'Apple'),
    (r'\b(Oracle|Java|JDK|WebLogic|Solaris|MySQL|VirtualBox)\b', 'Oracle'),
    (r'\b(IBM|WebSphere|Db2|QRadar|AIX|Informix)\b', 'IBM'),
    (r'\b(SAP|NetWeaver|S/4HANA|Commerce Cloud|HANA|Extended Passport)\b', 'SAP'),
    (r'\b(VMware|vCenter|ESXi|Horizon|Cloud Foundation|Spring)\b', 'VMware'),
    (r'\b(Citrix|NetScaler|Workspace)\b', 'Citrix'),
    (r'\b(Salesforce)\b', 'Salesforce'),
    (r'\b(ServiceNow)\b', 'ServiceNow'),
    (r'\b(Atlassian|Jira|Confluence|Bitbucket)\b', 'Atlassian'),
    (r'\b(JetBrains|YouTrack|IntelliJ|TeamCity)\b', 'JetBrains'),
    (r'\b(Zoom)\b', 'Zoom'),
    (r'\b(Dell|iDRAC|Wyse|Alienware|EMC)\b', 'Dell'),
    (r'\b(HP|Hewlett-Packard|HPE|Aruba)\b', 'HP'),
    (r'\b(Lenovo)\b', 'Lenovo'),
    (r'\b(Asus)\b', 'Asus'),
    (r'\b(Samsung|DualDAR|Knox SMR|Knox|libimagecodec)\b', 'Samsung'),
    (r'\b(Huawei|openHiTLS)\b', 'Huawei'),
    (r'\b(Xiaomi)\b', 'Xiaomi'),
    (r'\b(Amazon|AWS|Athena|Neptune)\b', 'Amazon AWS'),
    (r'\b(Siemens|Reyrolle|SIMATIC|SCALANCE|SINAMICS|Desigo|Sycron)\b', 'Siemens'),
    (r'\b(NEC|UNIVERGE)\b', 'NEC'),
    (r'\b(Hitachi|Cosminexus)\b', 'Hitachi'),
    (r'\b(ConnectWise|ScreenConnect)\b', 'ConnectWise'),
    (r'\b(Commvault|Command Center)\b', 'Commvault'),
    (r'\b(N-able|N-central)\b', 'N-able'),
    (r'\b(Auth0)\b', 'Auth0'),
    (r'\b(Tenable|Sensor Proxy)\b', 'Tenable'),
    (r'\b(Menulux)\b', 'Menulux'),
    (r'\b(Telenia Software|TVox)\b', 'Telenia Software'),
    (r'\b(Tranquil IT|WAPT|Wapt Server)\b', 'Tranquil IT'),
    (r'\b(SmartIT)\b', 'SmartIT'),
    (r'\b(Next4Biz)\b', 'Next4Biz'),

    # 4. Networking, Hardware & IoT
    (r'\b(Cisco|IOS XE|ASA|Firepower|Webex|Meraki)\b', 'Cisco'),
    (r'\b(Fortinet|FortiGate|FortiOS|FortiManager|FortiClient)\b', 'Fortinet'),
    (r'\b(Palo Alto|PAN-OS|GlobalProtect)\b', 'Palo Alto'),
    (r'\b(SonicWall|SMA|SonicOS)\b', 'SonicWall'),
    (r'\b(Check Point|Quantum|Gaia)\b', 'Check Point'),
    (r'\b(Ivanti|Connect Secure|Policy Secure|EPMM|Avalanche)\b', 'Ivanti'),
    (r'\b(F5|BIG-IP)\b', 'F5'),
    (r'\b(Juniper|Junos)\b', 'Juniper'),
    (r'\b(MikroTik|RouterOS)\b', 'MikroTik'),
    (r'\b(Ubiquiti|UniFi|EdgeRouter|EdgeMAX|EdgeSwitch|UID Enterprise Agent)\b', 'Ubiquiti'),
    (r'\b(Zyxel)\b', 'Zyxel'),
    (r'\b(TP-Link|Tether|Deco)\b', 'TP-Link'),
    (r'\b(D-Link)\b', 'D-Link'),
    (r'\b(Netgear|Nighthawk|Orbi)\b', 'Netgear'),
    (r'\b(Tenda|Tneda)\b', 'Tenda'),
    (r'\b(Wavlink)\b', 'Wavlink'),
    (r'\b(TRENDnet)\b', 'TRENDnet'),
    (r'\b(ipTIME|EFM ipTIME)\b', 'ipTIME'),
    (r'\b(Dahua)\b', 'Dahua'),
    (r'\b(Hikvision)\b', 'Hikvision'),
    (r'\b(Trueview)\b', 'Trueview'),
    (r'\b(Zebra)\b', 'Zebra'),
    (r'\b(DJI)\b', 'DJI'),
    (r'\b(Baylan)\b', 'Baylan'),
    (r'\b(SteelSeries)\b', 'SteelSeries'),
    (r'\b(WatchGuard|Fireware OS|Dimension)\b', 'WatchGuard'),
    (r'\b(TOTOLINK)\b', 'TOTOLINK'),
    (r'\b(LB-link|LBlink)\b', 'LB-link'),
    (r'\b(Ebyte)\b', 'Ebyte'),
    (r'\b(Zbtlink|MoreQuick|MT7620N)\b', 'Zbtlink'),
    (r'\b(AOS-CX|Aruba)\b', 'Aruba / HPE'),
    (r'\b(RSLinx|Rockwell Automation)\b', 'Rockwell Automation'),
    (r'\b(Phison|PS3111)\b', 'Phison'),
    (r'\b(QVidium)\b', 'QVidium'),
    (r'\b(Xiiaozet)\b', 'Xiiaozet'),
    (r'\b(NetStaX)\b', 'NetStaX'),
    (r'\b(OpenRISC|OR1200)\b', 'OpenRISC'),
    (r'\b(Colorful|iGameCenter)\b', 'Colorful'),
    (r'\b(U-Boot|DENX)\b', 'DENX / U-Boot'),
    (r'\b(ASE2000)\b', 'ASE2000'),
    (r'\b(ZTE|ZXDU\w*)\b', 'ZTE'),
    (r'\b(Sauter|moduWeb)\b', 'Sauter Controls'),
    (r'\b(Veeam|Veeam ONE)\b', 'Veeam'),
    (r'\b(Team Password Manager)\b', 'Team Password Manager'),
    (r'\b(Funiture)\b', 'Funiture'),
    (r'\b(Cyrus|Sieve|editheader)\b', 'Cyrus IMAP / Sieve'),
    (r'\b(ERP system|ERP Web System)\b', 'Enterprise ERP'),

    # 5. DevOps, Cloud Infrastructure & Storage
    (r'\b(Kubernetes|k8s|kubelet|KubeVirt|HelmRelease|Helm|managedcluster|multicloud cluster|StackGres|Submariner)\b', 'Kubernetes / Cloud Native'),
    (r'\b(Kyverno)\b', 'Kyverno'),
    (r'\b(Wazuh|OSSEC)\b', 'Wazuh'),
    (r'\b(Ceph|cephadm)\b', 'Ceph'),
    (r'\b(LibreNMS)\b', 'LibreNMS'),
    (r'\b(Argo Rollouts|ArgoCD|Argo)\b', 'Argo'),
    (r'\b(JFrog|Artifactory)\b', 'JFrog'),
    (r'\b(Redpanda)\b', 'Redpanda'),
    (r'\b(NebulaGraph)\b', 'NebulaGraph'),
    (r'\b(Liman)\b', 'Liman'),
    (r'\b(Liderahenk)\b', 'Liderahenk'),
    (r'\b(super-diamond|super-diamond-server)\b', 'super-diamond'),
    (r'\b(disconf)\b', 'disconf'),
    (r'\b(JetLinks|jetlinks)\b', 'JetLinks'),
    (r'\b(DWSurvey)\b', 'DWSurvey'),
    (r'\b(Zyplayer|Zyplayer-Doc)\b', 'Zyplayer'),
    (r'\b(Hulumi|@hulumi|holumi)\b', 'Hulumi'),
    (r'\b(Stomp)\b', 'Stomp'),
    (r'\b(Docker|Containerd|Kraken)\b', 'Docker'),
    (r'\b(Incus)\b', 'Incus'),
    (r'\b(OpenStack)\b', 'OpenStack'),
    (r'\b(Proxmox)\b', 'Proxmox'),
    (r'\b(TrueNAS|FreeNAS|OSNEXUS|QuantaStor)\b', 'OSNEXUS / Storage OSS'),
    (r'\b(QNAP|QTS|QuTS)\b', 'QNAP'),
    (r'\b(Synology|DSM)\b', 'Synology'),
    (r'\b(OpenWrt)\b', 'OpenWrt'),
    (r'\b(pfSense|OPNsense)\b', 'pfSense / OPNsense'),
    (r'\b(WireGuard|OpenVPN)\b', 'OpenVPN / WireGuard'),
    (r'\b(GitLab)\b', 'GitLab'),
    (r'\b(GitHub)\b', 'GitHub'),
    (r'\b(Jenkins)\b', 'Jenkins'),

    # 6. Database, CMS & Web Frameworks
    (r'\b(Apache|Tomcat|HTTP Server|Struts|Log4j|ActiveMQ|Kafka|Airflow|Superset|Hadoop)\b', 'Apache'),
    (r'\b(Nginx)\b', 'Nginx'),
    (r'\b(PostgreSQL)\b', 'PostgreSQL'),
    (r'\b(MongoDB)\b', 'MongoDB'),
    (r'\b(Redis)\b', 'Redis'),
    (r'\b(ArcadeDB)\b', 'ArcadeDB'),
    (r'\b(Datiphy)\b', 'Datiphy'),
    (r'\b(Elasticsearch|Kibana|Logstash|Elastic)\b', 'Elastic'),
    (r'\b(Splunk)\b', 'Splunk'),
    (r'\b(Grafana)\b', 'Grafana'),
    (r'\b(SolarWinds|Orion)\b', 'SolarWinds'),
    (r'\b(Logsign)\b', 'Logsign'),
    (r'\b(Zimbra)\b', 'Zimbra'),
    (r'\b(BookStack)\b', 'BookStack'),
    (r'\b(Plone)\b', 'Plone'),
    (r'\b(SOY CMS)\b', 'SOY CMS'),
    (r'\b(AVideo)\b', 'AVideo'),
    (r'\b(Trilium)\b', 'Trilium'),
    (r'\b(Cloud Commander)\b', 'Cloud Commander'),
    (r'\b(Slim framework|Slim Framework)\b', 'Slim Framework'),
    (r'\b(TarsWeb|Tencent TARS)\b', 'Tencent TARS'),
    (r'\b(3DSwymer|Dassault Systemes)\b', 'Dassault Systemes'),
    (r'\b(Eclipse Lyo|Eclipse)\b', 'Eclipse'),
    (r'\b(Talassoft)\b', 'Talassoft'),
    (r'\b(Teracity|E-OSB)\b', 'Teracity'),
    (r'\b(TRtek)\b', 'TRtek'),
    (r'\b(Klemsan|KIO)\b', 'Klemsan'),
    (r'\b(Epayco)\b', 'Epayco'),
    (r'\b(Flowintel)\b', 'Flowintel'),
    (r'\b(Fluent Boards)\b', 'Fluent Boards'),
    (r'\b(Beautiful Taxonomy Filters|Throws SPAM Away|Visitor Traffic Real Time Statistics|Newspapers X|Hash Form|SMS and newsletter)\b', 'WordPress'),
    (r'\b(Tribuna|Prensa|apitribuna|apiprensa)\b', 'Prensa / Tribuna CMS'),

    # 7. AI, Security, Tools & Open Source Libraries
    (r'\b(Cohere|Coherent North AI|Cohere North AI)\b', 'Cohere AI'),
    (r'\b(FastGPT)\b', 'FastGPT'),
    (r'\b(BerriAI|LiteLLM)\b', 'BerriAI'),
    (r'\b(gpt-researcher|gpt_researcher)\b', 'gpt-researcher'),
    (r'\b(Kotaemon)\b', 'Kotaemon'),
    (r'\b(Hermes Agent)\b', 'Hermes Agent'),
    (r'\b(Yu AI|Code Mother)\b', 'Yu AI'),
    (r'\b(23blocks|AI Maestro)\b', '23blocks'),
    (r'\b(MCP-router|MCP-HTTP-Server|UI-TARS|Telnyx MCP|Argocd-MCP|MCP server)\b', 'Model Context Protocol (MCP)'),
    (r'\b(Onyx AI|MemOS|CodeWhale|FUXA|GBIF|Capella|Omnigent|Xinference|unstructured)\b', 'AI & Data Platforms'),
    (r'\b(Mozilla|Firefox|Thunderbird|Gecko)\b', 'Mozilla'),
    (r'\b(OpenSSL|openssl_encrypt)\b', 'OpenSSL'),
    (r'\b(Bouncy Castle|bc-fips|bctls-fips)\b', 'Bouncy Castle'),
    (r'\b(better-auth)\b', 'better-auth'),
    (r'\b(Rodauth)\b', 'Rodauth'),
    (r'\b(EFence)\b', 'EFence'),
    (r'\b(Shinobi)\b', 'Shinobi'),
    (r'\b(Kerberos)\b', 'MIT Kerberos'),
    (r'\b(FreeIPA|Linux|Debian|Ubuntu|Red Hat|RHEL|CentOS|Fedora|SUSE|Alpine|Kernel)\b', 'Linux / FreeIPA'),
    (r'\b(authentik|Bastillion)\b', 'authentik / Bastillion'),
    (r'\b(SpiderFoot)\b', 'SpiderFoot'),
    (r'\b(AzuraCast|zuraCast)\b', 'AzuraCast'),
    (r'\b(JeecgBoot)\b', 'JeecgBoot'),
    (r'\b(xdocreport)\b', 'xdocreport'),
    (r'\b(OSSRS|SRS)\b', 'OSSRS'),
    (r'\b(Brainformatik)\b', 'Brainformatik'),
    (r'\b(Frappe|ERPNext)\b', 'Frappe / ERPNext'),
    (r'\b(DataHub|LinkedIn)\b', 'DataHub / LinkedIn'),
    (r'\b(Lemur|Netflix)\b', 'Netflix / Lemur'),
    (r'\b(S2OPC|Systerel)\b', 'Systerel / S2OPC'),
    (r'\b(GAPTEQ)\b', 'GAPTEQ'),
    (r'\b(Squirro)\b', 'Squirro'),
    (r'\b(T-Systems|ImageMaster)\b', 'T-Systems'),
    (r'\b(PTC|Windchill|FlexPLM)\b', 'PTC'),
    (r'\b(Mongoose)\b', 'Mongoose'),
    (r'\b(JSONata)\b', 'JSONata'),
    (r'\b(libevent|libre)\b', 'libevent / libre'),
    (r'\b(Nezha)\b', 'Nezha'),
    (r'\b(Paperclip)\b', 'Paperclip'),
    (r'\b(exceljs|vm2|Seroval|Express\.js|Node\.js|NodeJS|npm)\b', 'Node.js / JS OSS'),
    (r'\b(Nodemailer)\b', 'Nodemailer'),
    (r'\b(PyAthena|JustHTML|justhtml|Python|PyPI|Django|Flask|FastAPI|NLTK)\b', 'Python OSS'),
    (r'\b(ADOdb|PHP|PECL|Composer|PHPMailer)\b', 'PHP OSS'),
    (r'\b(Perl|XML::Sig|Net::SAML2|CPAN)\b', 'Perl'),
    (r'\b(Rust|Cargo)\b', 'Rust OSS'),
    (r'\b(Golang|Go)\b', 'Golang'),
    (r'\b(Fastify|middie|@fastify)\b', 'Fastify'),
    (r'\b(Dropbox|samly)\b', 'Dropbox / samly'),
    (r'\b(OpenRGB)\b', 'OpenRGB'),
    (r'\b(qTox|Tox)\b', 'qTox'),
    (r'\b(NUMail)\b', 'NUMail'),
    (r'\b(Pocket)\b', 'Pocket'),
    (r'\b(Netis)\b', 'Netis'),
    (r'\b(Voltronic Power|SNMP Web Pro)\b', 'Voltronic Power'),
    (r'\b(MBS-Solutions|X-Serie Gateway)\b', 'MBS-Solutions'),
    (r'\b(CPTrans|CPTrans-ME-X)\b', 'CPTrans'),
    (r'\b(IXON|IXON Cloud)\b', 'IXON'),
    (r'\b(OCS|Open Communication System)\b', 'OCS'),
    (r'\b(DeepSeek)\b', 'DeepSeek'),
    (r'\b(FastChat)\b', 'FastChat'),
    (r'\b(SadTalker)\b', 'SadTalker'),
    (r'\b(TEN Framework)\b', 'TEN Framework'),
    (r'\b(DocsGPT)\b', 'DocsGPT'),
    (r'\b(AimStack|Aim tracking)\b', 'AimStack'),
    (r'\b(Traefik|digestAuth)\b', 'Traefik Labs'),
    (r'\b(curl|libcurl)\b', 'curl'),
    (r'\b(FreeType|ftsmooth)\b', 'FreeType'),
    (r'\b(FreeIPMI)\b', 'FreeIPMI'),
    (r'\b(MISP)\b', 'MISP'),
    (r'\b(MapLibre)\b', 'MapLibre'),
    (r'\b(PowerJob)\b', 'PowerJob'),
    (r'\b(Prevail|eBPF Verifier)\b', 'Prevail'),
    (r'\b(Joro|Joro Framework)\b', 'Joro'),
    (r'\b(FIDO Alliance|FIDO2)\b', 'FIDO Alliance'),
    (r'\b(Authorizer)\b', 'Authorizer'),
    (r'\b(MOOS-IvP|MOOS_IvP|MOOS)\b', 'MOOS-IvP'),
    (r'\b(Taipy)\b', 'Taipy'),
    (r'\b(SQL Chat)\b', 'SQL Chat'),
    (r'\b(Nango)\b', 'Nango'),
    (r'\b(MojoX)\b', 'MojoX'),
    (r'\b(OpenIDC|cjose)\b', 'OpenIDC'),
    (r'\b(OpenMAIC)\b', 'OpenMAIC'),
    (r'\b(MicroXR)\b', 'MicroXR'),
    (r'\b(Hawtio)\b', 'Hawtio'),
    (r'\b(Cua|computer-server)\b', 'Cua'),
    (r'\b(knowns)\b', 'knowns'),
    (r'\b(Digital-Infrastructure)\b', 'Digital-Infrastructure'),
    (r'\b(Movie_Recommend)\b', 'Movie_Recommend'),
    (r'\b(BiHayat)\b', 'BiHayat'),
    (r'\b(zerox)\b', 'zerox'),
    (r'\b(xiaobei)\b', 'xiaobei'),
    (r'\b(sift\.js|sift)\b', 'sift.js'),
]


def _ekstrak_vendor_dari_deskripsi(deskripsi: str, daftar_vendor_dikenal: List[str]) -> Optional[str]:
    """
    Fallback saat CPE kosong: mencari nama vendor yang dikenal di dalam
    teks deskripsi CVE dengan pencocokan aturan ekosistem dan kamus vendor.
    """
    if not deskripsi:
        return None

    # 1. Cek aturan ekosistem & pola regex
    for pola, vendor_name in _ATURAN_EKOSISTEM_VENDOR:
        if re.search(pola, deskripsi, re.IGNORECASE):
            return vendor_name

    # 2. Cek daftar vendor dikenal dari config.yaml (dengan regex word boundary)
    for vendor in daftar_vendor_dikenal:
        if len(vendor) <= 3:
            # Kata pendek (Go, PHP, HP, SAP) wajib cocok persis batas kata
            if re.search(r'\b' + re.escape(vendor) + r'\b', deskripsi, re.IGNORECASE):
                return vendor
        else:
            if re.search(r'\b' + re.escape(vendor) + r'\b', deskripsi, re.IGNORECASE):
                return vendor

    return None


def bersihkan_nama_produk(nama: str) -> str:
    """Membersihkan nama produk dari kata-kata noise dan tanda baca."""
    if not nama:
        return ""
    # Hapus trailing noise
    pola_noise = r'\s+(yang|terdampak|memiliki|adalah|sebelum|versi|dengan|untuk|pada|di|dalam|tanpa|oleh|terkena|menggunakan|berjalan|sebagai|ke|dan|atau|hook|bazaar|sebelumnya|saat|ketika|karena|pro|\d+[\.\d]*)$'
    for _ in range(3):
        nama = re.sub(pola_noise, '', nama, flags=re.IGNORECASE).strip()
    
    # Hapus prefix noise
    pola_prefix = r'^(sistem|produk|plugin|ekstensi|modul|aplikasi|library|software|yang\s+menggunakan)\s+'
    for _ in range(2):
        nama = re.sub(pola_prefix, '', nama, flags=re.IGNORECASE).strip()

    # Potong jika ada titik / koma / newline / kata Jenis
    if '\n' in nama:
        nama = nama.split('\n')[0].strip()
    if 'Jenis' in nama:
        nama = nama.split('Jenis')[0].strip()
    if '.' in nama:
        nama = nama.split('.')[0].strip()
    if ',' in nama:
        nama = nama.split(',')[0].strip()

    nama = nama.strip(" .,-:/")
    if nama.upper() in ["AWS S3", "AMAZON S3"]:
        return "Amazon S3"
    if nama.startswith("Golang ") and len(nama) > 7:
        nama = nama[7:].strip()
    if re.search(r'\bT16000M\s+\d+', nama):
        nama = re.sub(r'\s+\d+$', '', nama).strip()

    return nama


def ekstrak_produk_cve(deskripsi_en: str = "", narasi_id: str = "", vendor: str = "") -> str:
    """
    Ekstrak nama produk spesifik yang bersih dan bermakna dari deskripsi NVD atau narasi LLM.
    Tidak akan pernah mengembalikan '(lihat deskripsi)' atau '-'.
    """
    teks_gabung = f"{deskripsi_en or ''} {narasi_id or ''}".strip()
    if not teks_gabung:
        return vendor.split('/')[0].strip() if vendor and vendor not in ["-", "(lihat deskripsi)", "Lainnya / Belum Teridentifikasi"] else "-"

    # 1. Cek aturan ekosistem & pola regex khusus
    for pola, v_name in _ATURAN_EKOSISTEM_VENDOR:
        m = re.search(pola, teks_gabung, re.IGNORECASE)
        if m:
            matched = m.group(0).strip()
            m_full = re.search(rf'\b({re.escape(matched)}(?:\s+[A-Z0-9][a-zA-Z0-9_\-\.]+){{1,3}})\b', teks_gabung)
            cand = m_full.group(1) if m_full else matched
            cand_clean = bersihkan_nama_produk(cand)
            if cand_clean and len(cand_clean) >= 2 and cand_clean.lower() not in ['wordpress', 'php', 'python', 'rust', 'golang', 'node.js', 'microsoft', 'adobe', 'google', 'apple', 'apache', 'linux']:
                return cand_clean

    # 2. Cek pola deskripsi NVD umum (English)
    if deskripsi_en:
        m_in = re.search(r'\bIn\s+([A-Z0-9][a-zA-Z0-9_\-\.\s]{2,30}?)\s+(?:before|prior|version|versions|through|up to|\d)', deskripsi_en, re.IGNORECASE)
        if m_in:
            cand = bersihkan_nama_produk(m_in.group(1))
            if cand and cand.lower() not in ['all', 'some', 'the', 'this', 'certain', 'various']:
                return cand

        m_pkg = re.search(r'\b([A-Za-z0-9_\-\.]{2,30})\s+\((?:npm|pypi|crate|gem|package|wordpress plugin)\)', deskripsi_en, re.IGNORECASE)
        if m_pkg:
            cand = bersihkan_nama_produk(m_pkg.group(1))
            if cand:
                return cand

        m_start = re.search(r'^([A-Z0-9][a-zA-Z0-9_\-\.\s]{2,30}?)\s+(?:versions?|prior to|before|contains?|allows?|is affected)\b', deskripsi_en, re.IGNORECASE)
        if m_start:
            cand = bersihkan_nama_produk(m_start.group(1))
            if cand and not cand.startswith("CVE-") and cand.lower() not in ['the', 'this', 'an', 'all']:
                return cand

    # 3. Cek pola narasi LLM (Bahasa Indonesia)
    if narasi_id:
        m_nar = re.search(r'Produk\s+(?:yang\s+)?(?:sistem\s+)?terdampak\s+adalah\s+(?:sistem\s+|plugin\s+|ekstensi\s+|aplikasi\s+|software\s+)?([A-Z0-9][A-Za-z0-9_\-\.\s]{2,30}?)(?:\s+versi|\s+dengan|\s+yang|\s+pada|\s+untuk|\.|\,)', narasi_id, re.IGNORECASE)
        if m_nar:
            cand = bersihkan_nama_produk(m_nar.group(1))
            if cand and cand.lower() not in ['sistem', 'aplikasi', 'perangkat lunak', 'plugin', 'server', 'komponen']:
                return cand

        m_wp = re.search(r'plugin\s+([A-Z0-9][A-Za-z0-9_\-\.\s]{2,30}?)\s+(?:untuk|pada|di)\s+WordPress', narasi_id, re.IGNORECASE)
        if m_wp:
            cand = bersihkan_nama_produk(m_wp.group(1))
            if cand:
                return cand

    # 4. Fallback ke vendor
    if vendor and vendor not in ["-", "(lihat deskripsi)", "Lainnya / Belum Teridentifikasi"]:
        return vendor.split('/')[0].strip()

    return "-"


def _ekstrak_vendor_produk(cve: dict, daftar_vendor_dikenal: List[str]) -> tuple:
    """
    Prioritas penentuan vendor & produk:
    1. Data CPE terstruktur (paling akurat, tapi sering kosong).
    2. Pencarian nama vendor dikenal di teks deskripsi (fallback).
    3. Label 'Lainnya / Belum Teridentifikasi' jika keduanya gagal.
    """
    hasil_cpe = _ekstrak_vendor_dari_cpe(cve)
    if hasil_cpe:
        vendor_cpe, produk_cpe = hasil_cpe[0], hasil_cpe[1]
        # Normalisasi vendor CPE jika masuk ekosistem khusus
        for pola, vendor_name in _ATURAN_EKOSISTEM_VENDOR:
            if re.search(pola, f"{vendor_cpe} {produk_cpe}", re.IGNORECASE):
                return vendor_name, produk_cpe
        return vendor_cpe, produk_cpe

    deskripsi_list = cve.get("descriptions", [])
    deskripsi_en = next((d["value"] for d in deskripsi_list if d.get("lang") == "en"), "")
    vendor_dari_teks = _ekstrak_vendor_dari_deskripsi(deskripsi_en, daftar_vendor_dikenal)
    if not vendor_dari_teks:
        # Coba cek link referensi jika deskripsi belum berhasil mencocokkan
        ref_teks = " ".join([r.get("url", "") for r in cve.get("references", [])])
        if ref_teks:
            vendor_dari_teks = _ekstrak_vendor_dari_deskripsi(f"{deskripsi_en} {ref_teks}", daftar_vendor_dikenal)

    if vendor_dari_teks:
        produk_ekstrak = ekstrak_produk_cve(deskripsi_en=deskripsi_en, vendor=vendor_dari_teks)
        return vendor_dari_teks, produk_ekstrak

    return "Lainnya / Belum Teridentifikasi", "-"


def _parse_item_cve(item: dict, daftar_vendor_dikenal: List[str]) -> Optional[dict]:
    """Mengubah satu objek 'vulnerability' dari respons NVD menjadi dict ringkas."""
    cve = item.get("cve", {})
    cve_id = cve.get("id")
    if not cve_id:
        return None

    deskripsi_list = cve.get("descriptions", [])
    deskripsi_en = next((d["value"] for d in deskripsi_list if d.get("lang") == "en"), "")

    metrics = cve.get("metrics", {})
    skor = _ekstrak_skor_cvss(metrics)
    severity = _ekstrak_severity(metrics)
    vendor, produk = _ekstrak_vendor_produk(cve, daftar_vendor_dikenal)

    return {
        "cve_id": cve_id,
        "deskripsi": deskripsi_en,
        "skor_cvss": skor,
        "severity": severity,
        "vendor": vendor,
        "produk": produk,
        "tanggal_publish": cve.get("published", "")[:19].replace("T", " "),
        "link": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
    }

def ambil_cve_terbaru(
    base_url: str,
    window_hours: int = 24,
    min_cvss_score: float = 7.0,
    daftar_vendor_dikenal: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    timeout: int = 20,
) -> pd.DataFrame:
    """
    Mengambil CVE yang dipublikasikan dalam N jam terakhir dari NVD API,
    difilter berdasarkan skor CVSS minimum.

    NVD API membatasi rentang query maksimal 120 hari per request dan
    menggunakan pagination (default 2000 hasil/halaman), jadi loop
    pagination tetap disiapkan meskipun untuk window 24 jam biasanya
    hasilnya jauh di bawah itu.
    """
    daftar_vendor_dikenal = daftar_vendor_dikenal or []
    batas_akhir = datetime.now(timezone.utc)
    batas_awal = batas_akhir - timedelta(hours=window_hours)

    headers = {"apiKey": api_key} if api_key else {}
    jeda_request = 6 if not api_key else 0.6  # patuhi rate limit resmi NVD
    session = buat_session_retry(max_retry=3, backoff_factor=2.0)

    hasil_semua = []
    start_index = 0
    total_hasil = None
    data_lengkap = True
    jumlah_halaman_gagal = 0
    MAKS_HALAMAN_GAGAL = 5

    UKURAN_HALAMAN = 500

    while total_hasil is None or start_index < total_hasil:
        params = {
            "pubStartDate": batas_awal.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": batas_akhir.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "startIndex": start_index,
            "resultsPerPage": UKURAN_HALAMAN,
        }
        try:
            resp = session.get(base_url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            jumlah_halaman_gagal += 1
            data_lengkap = False
            logger.error(
                f"GAGAL mengambil halaman CVE (startIndex={start_index}): {e}. "
                f"Halaman ini DILEWATI, lanjut coba halaman berikutnya "
                f"({jumlah_halaman_gagal}/{MAKS_HALAMAN_GAGAL} kegagalan sejauh ini)."
            )

            if total_hasil is None:
                # Halaman PERTAMA yang gagal - kita bahkan belum tahu total_hasil,
                # jadi tidak ada cara aman melanjutkan pagination. Terpaksa berhenti.
                logger.error("Halaman pertama gagal diambil, tidak bisa melanjutkan (total_hasil belum diketahui).")
                break

            if jumlah_halaman_gagal >= MAKS_HALAMAN_GAGAL:
                logger.error(f"Sudah {MAKS_HALAMAN_GAGAL} halaman gagal berturut-turut, berhenti mencoba lebih lanjut.")
                break

            start_index += UKURAN_HALAMAN  # lompat, anggap sudah "dilewati"
            time.sleep(jeda_request)
            continue

        data = resp.json()
        total_hasil = data.get("totalResults", 0)
        vulnerabilities = data.get("vulnerabilities", [])

        for item in vulnerabilities:
            parsed = _parse_item_cve(item, daftar_vendor_dikenal)
            if parsed:
                hasil_semua.append(parsed)

        start_index += len(vulnerabilities) if vulnerabilities else UKURAN_HALAMAN
        if start_index < total_hasil:
            time.sleep(jeda_request)

    if data_lengkap:
        logger.info(f"Total CVE dipublikasikan dalam {window_hours} jam terakhir: {len(hasil_semua)} (LENGKAP).")
    else:
        logger.warning(
            f"Total CVE berhasil diambil: {len(hasil_semua)} dari total {total_hasil or '?'} yang seharusnya ada "
            f"({jumlah_halaman_gagal} halaman gagal/dilewati - data TIDAK LENGKAP)."
        )

    df = pd.DataFrame(hasil_semua)
    if df.empty:
        return df
    
    # Filter berdasarkan skor CVSS minimum DAN severity CRITICAL saja
    df_filtered = df[
        (df["skor_cvss"].fillna(0) >= min_cvss_score) & (df["severity"] == "CRITICAL")
    ].reset_index(drop=True)
    logger.info(
        f"Setelah filter CVSS >= {min_cvss_score} DAN severity CRITICAL: "
        f"{len(df_filtered)} CVE (dari {len(df)} total)."
    )
    return df_filtered

def kelompokkan_cve_per_vendor(df: pd.DataFrame) -> List[dict]:
    """
    Mengelompokkan CVE CRITICAL per vendor, diurutkan: vendor dengan
    jumlah CVE terbanyak di atas. Di dalam grup, skor CVSS tertinggi
    diutamakan.
    """
    if df.empty:
        return []

    grup_hasil = []
    for vendor, grup in df.groupby("vendor"):
        grup_terurut = grup.sort_values(by="skor_cvss", ascending=False)
        grup_hasil.append({
            "vendor": vendor,
            "jumlah_critical": len(grup_terurut),
            "cve_list": grup_terurut.to_dict("records"),
        })

    grup_hasil.sort(key=lambda g: (-g["jumlah_critical"], g["vendor"]))
    return grup_hasil

def susun_struktur_digest_cve(df: pd.DataFrame) -> dict:
    """
    Menyusun struktur akhir CVE untuk kebutuhan digest. Karena sumber CVE
    sudah difilter CRITICAL-only sejak ambil_cve_terbaru(), fungsi ini
    cuma punya 2 mode:
    - Tidak ada CVE CRITICAL sama sekali -> mode 'kosong'
    - Ada CVE CRITICAL                   -> mode 'ada_critical': semua
      dikelompokkan per vendor & dinarasikan lengkap oleh LLM.
    """
    if df.empty:
        return {"mode": "kosong"}

    grup_vendor_critical = kelompokkan_cve_per_vendor(df)

    return {
        "mode": "ada_critical",
        "grup_critical": grup_vendor_critical,
        "jumlah_critical_total": len(df),
    }