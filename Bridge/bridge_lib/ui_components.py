import adsk.core
import bridge_config as config

_panels_created = []
_tabs_created = []


def create_ui(app: adsk.core.Application):
    ui = app.userInterface

    from bridge_commands import register_commands

    register_commands(ui)

    for ws_id in config.TARGET_WORKSPACES:
        ws = ui.workspaces.itemById(ws_id)
        if ws is None:
            continue

        tab = ws.toolbarTabs.itemById(config.TOOLBAR_TAB_ID)
        if tab is None:
            tab = ws.toolbarTabs.add(config.TOOLBAR_TAB_ID, "Bridge")
            _tabs_created.append(tab)

        panel = tab.toolbarPanels.itemById(config.TOOLBAR_PANEL_ID)
        if panel is None:
            panel = tab.toolbarPanels.add(config.TOOLBAR_PANEL_ID, "Infab")
            _panels_created.append(panel)

        cmd_def = ui.commandDefinitions.itemById(config.CMD_BRIDGE)
        if cmd_def:
            ctrl = panel.controls.itemById(config.CMD_BRIDGE)
            if not ctrl:
                ctrl = panel.controls.addCommand(cmd_def)
            if ctrl:
                ctrl.isVisible = True
                ctrl.isPromoted = True
                ctrl.isPromotedByDefault = True

        log_def = ui.commandDefinitions.itemById(config.CMD_VIEW_LOG)
        if log_def:
            ctrl = panel.controls.itemById(config.CMD_VIEW_LOG)
            if not ctrl:
                ctrl = panel.controls.addCommand(log_def)
            if ctrl:
                ctrl.isVisible = True


def destroy_ui(app: adsk.core.Application):
    ui = app.userInterface

    for panel in _panels_created:
        try:
            panel.deleteMe()
        except Exception:
            pass
    _panels_created.clear()

    for tab in _tabs_created:
        try:
            tab.deleteMe()
        except Exception:
            pass
    _tabs_created.clear()

    from bridge_commands import unregister_commands

    unregister_commands(ui)
