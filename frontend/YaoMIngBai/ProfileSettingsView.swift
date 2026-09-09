import SwiftUI

struct ProfileSettingsView: View {
    @EnvironmentObject private var app: AppState
    @AppStorage("elderMode") private var elderMode = false
    @AppStorage("voiceEnabled") private var voiceEnabled = true
    @AppStorage("highContrast") private var highContrast = false

    var showBack: Bool = false

    var body: some View {
        ScrollPage(title: "我的", subtitle: "个人与设置", showBack: showBack, trailingSystemImage: "gearshape.fill") {
            YBCard {
                HStack(spacing: 12) {
                    EmojiCircle(emoji: "👩", size: 56)
                    VStack(alignment: .leading, spacing: 5) {
                        Text("家庭管理员")
                            .font(.system(size: 20, weight: .heavy, design: .rounded))
                        Text("管理家庭药箱、提醒和服药记录")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }
                    Spacer()
                    StatusPill(text: elderMode ? "老人模式" : "普通模式", color: elderMode ? .ybOrange : .ybPrimary)
                }
            }

            SettingGroup(title: "家庭管理") {
                SettingRow(icon: "👨‍👩‍👧", title: "家庭成员", subtitle: "查看、新增或删除家庭成员") {
                    app.switchToTab(.family)
                }
                SettingRow(icon: "📋", title: "服药记录", subtitle: "查看今日与历史确认记录") {
                    app.path.append(Route.medicationRecords)
                }
            }

            YBCard {
                Text("老人模式")
                    .font(.ybCardTitle)
                Toggle("切换为老人专用界面", isOn: $elderMode)
                    .font(.ybBody)
                    .tint(.ybPrimary)
                Text("开启后， App 会切换成大字、少按钮、一步确认的老人模式。")
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
            }

            SettingGroup(title: "提醒与安全") {
                SettingRow(icon: "📋", title: "提醒列表", subtitle: "查看已经设置的全部服药计划") {
                    app.path.append(Route.reminderList)
                }
                SettingRow(icon: "🔔", title: "通知设置", subtitle: "服药、漏服、过期、低库存提醒") {}
                SettingRow(icon: "🛡️", title: "医疗安全声明", subtitle: "不诊断、不处方、不替代医生药师判断") {}
                SettingRow(icon: "🔒", title: "隐私设置", subtitle: "管理家庭共享和本地数据权限") {}
            }

            YBCard {
                Text("辅助功能")
                    .font(.ybCardTitle)
                Toggle("语音播报：卡片和提醒可一键朗读", isOn: $voiceEnabled)
                    .font(.ybBody)
                    .tint(.ybPrimary)
                Toggle("高对比模式：提高弱视和户外可读性", isOn: $highContrast)
                    .font(.ybBody)
                    .tint(.ybPrimary)
            }
        }
    }
}

struct SettingGroup<Content: View>: View {
    var title: String
    let content: Content

    init(title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }

    var body: some View {
        YBCard {
            Text(title)
                .font(.ybCardTitle)
            content
        }
    }
}

struct SettingRow: View {
    var icon: String
    var title: String
    var subtitle: String
    var action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                EmojiCircle(emoji: icon, size: 42)
                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.system(size: 15, weight: .heavy, design: .rounded))
                        .foregroundStyle(Color.ybText)
                    Text(subtitle)
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .heavy))
                    .foregroundStyle(Color.ybMuted)
            }
            .padding(.vertical, 4)
        }
        .buttonStyle(.plain)
    }
}
