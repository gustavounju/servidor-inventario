import glob

replacements = {
    "'dashboard'": "'dashboard.dashboard'",
    "'view_graphics'": "'dashboard.view_graphics'",
    "'view_cementerio'": "'dashboard.view_cementerio'",
    "'export_inventory'": "'dashboard.export_inventory'",
    "'pc_detail'": "'dashboard.pc_detail'",
    "'update_pc_infrastructure'": "'dashboard.update_pc_infrastructure'",
    "'add_task'": "'tasks.add_task'",
    "'mark_task_done'": "'tasks.mark_task_done'",
    "'delete_task'": "'tasks.delete_task'",
    "'assign_task'": "'tasks.assign_task'",
    "'create_loose_task'": "'tasks.create_loose_task'",
    "'add_technician'": "'tasks.add_technician'",
    "'delete_technician'": "'tasks.delete_technician'",
    "'migrate_generic_tasks'": "'tasks.migrate_generic_tasks'",
    "'add_manual_audit'": "'tasks.add_manual_audit'",
    "'report_tasks_completed'": "'tasks.report_tasks_completed'",
    "'report_tasks_completed_pdf'": "'tasks.report_tasks_completed_pdf'",
    "'export_inventory_pdf'": "'dashboard.export_inventory_pdf'",
    "'install_page'": "'setup.install_page'",
    "'download_certificate'": "'setup.download_certificate'",
    "'download_client_script'": "'setup.download_client_script'",
    "'download_client_launcher'": "'setup.download_client_launcher'",
    "'mobile_view'": "'api.mobile_view'", # wait, in bp_api, mobile_view was not prefixed by api.? It was just @bp_api.route, but blueprints prefix their names. Wait, where is mobile_view?
    "'mobile_scanner_view'": "'api.mobile_scanner_view'",
    "'stock_view'": "'stock.stock_view'",
    "'decommission_pc'": "'dashboard.decommission_pc'",
    "'reactivate_pc'": "'dashboard.reactivate_pc'",
    "'refresh_fueros'": "'dashboard.refresh_fueros'",
    "'delete_permanent_pc'": "'dashboard.delete_permanent_pc'",
    "'upload_manual_inventory'": "'api.upload_manual_inventory'"
}

for filepath in glob.glob("templates/**/*.html", recursive=True):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = content
    for old, new in replacements.items():
        # url_for('dashboard' -> url_for('dashboard.dashboard'
        new_content = new_content.replace(f"url_for({old}", f"url_for({new}")
        
        # url_for("dashboard" -> url_for("dashboard.dashboard"
        old_dbl = f'"{old.strip(chr(39))}"'
        new_dbl = f'"{new.strip(chr(39))}"'
        new_content = new_content.replace(f"url_for({old_dbl}", f"url_for({new_dbl}")
        
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filepath}")
