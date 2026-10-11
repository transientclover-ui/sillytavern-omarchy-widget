import QtQuick
import Quickshell
import Quickshell.Io
import qs.Ui

BarWidget {
    id: root
    moduleName: "local.rp-ai"
    property string serverState: "ERROR"
    readonly property string displayState: serverState === "READY" ? "Online" : serverState === "OFF" ? "Offline" : serverState === "STARTING" ? "Partial" : "Error"
    property string detail: "Waiting for status check"
    readonly property string controller: decodeURIComponent(Qt.resolvedUrl("rp-ai").toString().replace(/^file:\/\//, ""))
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight

    function refresh() {
        if (!poll.running) poll.running = true
    }
    Component.onCompleted: refresh()
    Timer {
        interval: 2000
        running: true
        repeat: true
        onTriggered: root.refresh()
    }
    Process {
        id: poll
        command: [root.controller, "status", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var result = JSON.parse(text)
                    root.serverState = result.state
                    root.detail = result.detail
                } catch (e) {
                    root.serverState = "ERROR"
                    root.detail = "Status command did not return valid JSON"
                }
            }
        }
        onExited: function(code, status) {
            if (code !== 0) {
                root.serverState = "ERROR"
                root.detail = "Status command failed"
            }
        }
    }
    WidgetButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        text: root.vertical ? "RP\n" + root.displayState : "RP AI " + root.displayState
        active: root.serverState === "ERROR"
        tooltipText: root.serverState + ": " + root.detail + (root.setting("clickToToggle", false) ? "\nClick to toggle inference" : "\nUse RP AI ON / RP AI OFF launchers")
        pressable: root.setting("clickToToggle", false)
        onPressed: function(mouseButton) {
            if (mouseButton === Qt.LeftButton && root.setting("clickToToggle", false))
                Quickshell.execDetached([root.controller, "toggle"])
        }
    }
    IpcHandler {
        target: "local.rp-ai"
        function state(): string { return root.serverState }
        function label(): string { return root.displayState }
        function refresh(): void { root.broadcast("refresh") }
    }
}
