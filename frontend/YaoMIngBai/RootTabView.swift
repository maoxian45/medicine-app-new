import SwiftUI

struct RootTabView: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("elderMode") private var elderMode = false

    var body: some View {
        Group {
            if elderMode {
                ElderModeShell()
            } else {
                NavigationStack(path: $app.path) {
                    TabView(selection: $app.selectedTab) {
                        HomeView()
                            .tabItem { Label(AppTab.home.title, systemImage: AppTab.home.icon) }
                            .tag(AppTab.home)

                        AddMedicineView(showBack: false)
                            .tabItem { Label(AppTab.scan.title, systemImage: AppTab.scan.icon) }
                            .tag(AppTab.scan)

                        FamilyMedicineBoxView(showBack: false)
                            .tabItem { Label(AppTab.box.title, systemImage: AppTab.box.icon) }
                            .tag(AppTab.box)

                        FamilyMembersView(showBack: false)
                            .tabItem { Label(AppTab.family.title, systemImage: AppTab.family.icon) }
                            .tag(AppTab.family)

                        ProfileSettingsView(showBack: false)
                            .tabItem { Label(AppTab.me.title, systemImage: AppTab.me.icon) }
                            .tag(AppTab.me)
                    }
                    .tint(.ybPrimary)
                    .navigationDestination(for: Route.self) { route in
                        routeView(route)
                    }
                }
            }
        }
        .onChange(of: elderMode) { enabled in
            if enabled {
                app.path = NavigationPath()
            }
        }
    }

    @ViewBuilder
    private func routeView(_ route: Route) -> some View {
        switch route {
        case .addMedicine: AddMedicineView(showBack: true)
        case .medicineCard: MedicineCardView()
        case .reminderSetting: ReminderSettingView()
        case .reminderList: ReminderListView()
        case .medicationAlarm: MedicationAlarmView()
        case .familyBox: FamilyMedicineBoxView(showBack: true)
        case .medicineDetail: MedicineDetailView()
        case .familyMembers: FamilyMembersView(showBack: true)
        case .elderStatus: ElderStatusView()
        case .childFeedingRecord(let memberName): ChildFeedingRecordView(memberName: memberName)
        case .medicationRecords: MedicationRecordsView()
        case .profileSettings: ProfileSettingsView(showBack: true)
        case .elderHome: ElderHomeView()
        case .elderAlarm: ElderAlarmView()
        case .elderMedicineDetail: ElderMedicineDetailView()
        case .elderMyMedicines: ElderMyMedicinesView()
        case .elderMissedDose: ElderMissedDoseView()
        case .elderContactFamily: ElderContactFamilyView()
        case .elderSettings: ElderSettingsView()
        }
    }
}
