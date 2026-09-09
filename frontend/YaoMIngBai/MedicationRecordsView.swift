import SwiftUI

struct MedicationRecordsView: View {
    @EnvironmentObject private var app: AppState
    @State private var memberFilter = "全部"

    private var memberOptions: [String] {
        let names = Set(app.records.map { record -> String in
            let parts = record.title.components(separatedBy: "·")
            return parts.count > 1 ? parts[1].trimmingCharacters(in: .whitespacesAndNewlines) : "我"
        })
        return ["全部"] + names.sorted()
    }

    private var filteredRecords: [DoseRecord] {
        guard memberFilter != "全部" else { return app.records }
        return app.records.filter { $0.title.contains(memberFilter) }
    }

    private var completedCount: Int {
        app.records.filter { $0.status.contains("已") }.count
    }

    var body: some View {
        ScrollPage(title: "服药记录", subtitle: "记录中心", showBack: true, trailingSystemImage: "checkmark.circle.fill") {
            HeroCard {
                Text("今日记录概览")
                    .font(.system(size: 20, weight: .heavy, design: .rounded))
                Text(app.records.isEmpty ? "今天还没有服药确认记录。" : "今天已有 \(app.records.count) 条服药确认记录。")
                    .font(.ybBody)
                    .opacity(0.92)

                HStack(spacing: 10) {
                    MetricTile(number: "\(completedCount)", title: "已服药", tint: .ybGreen)
                    MetricTile(number: "\(app.todayPending)", title: "待服药", tint: .ybOrange)
                    MetricTile(number: "\(app.records.count)", title: "全部记录", tint: .ybBlue)
                }
            }

            if memberOptions.count > 1 {
                YBCard {
                    SelectionBlock(title: "成员筛选", subtitle: "按记录对象", options: memberOptions, selected: $memberFilter)
                }
            }

            YBCard {
                SectionTitle(title: "记录列表", trailing: "共 \(filteredRecords.count) 条")
                if filteredRecords.isEmpty {
                    Text("暂无记录。可以在提醒列表或老人模式中确认服药后查看。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                } else {
                    ForEach(filteredRecords) { record in
                        VStack(spacing: 8) {
                            TimelineRow(time: record.time, title: record.title, detail: record.detail)
                            SecondaryButton(title: "点错了，取消这条记录", systemImage: "arrow.uturn.backward.circle.fill") {
                                app.cancelTaken(record: record)
                            }
                        }
                        Divider()
                    }
                }
            }
        }
        .refreshable {
            await app.refreshFromBackend()
        }
    }
}
