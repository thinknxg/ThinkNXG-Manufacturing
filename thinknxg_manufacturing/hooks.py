app_name = "thinknxg_manufacturing"
app_title = "ThinkNXG Manufacturing"
app_publisher = "ThinkNXG"
app_description = "KSSB UAE structural steel manufacturing demo dataset for ERPNext v16"
app_email = "teraboxneed@gmail.com"
app_license = "mit"
required_apps = ["erpnext"]

# Queue the ordered demo-data loader (skips anything already loaded).
after_install = "thinknxg_manufacturing.demo.autoload"
after_migrate = ["thinknxg_manufacturing.demo.autoload"]
