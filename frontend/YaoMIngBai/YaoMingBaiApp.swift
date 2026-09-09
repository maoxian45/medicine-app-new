import SwiftUI

@main
struct YaoMingBaiApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .environmentObject(appState)
                .task {
                    await appState.refreshFromBackend()
                }
        }
    }
}
