import SwiftUI

struct MedicineDetailView: View {
    @EnvironmentObject private var app: AppState
    @State private var showDeleteConfirm = false
    @State private var showEditSheet = false
    @State private var isDeleting = false
    @State private var isConfirming = false
    @State private var detailMessage = ""
    var medicine: Medicine { app.currentMedicine }

    private var groupedItems: [Medicine] {
        let matches = app.medicines.filter { $0.groupingKey == medicine.groupingKey }
        return matches.isEmpty ? [medicine] : matches
    }

    private var displayStock: String {
        Medicine.mergedStocks(groupedItems.map(\.stock))
    }

    private var displayStatus: String {
        groupedItems.count > 1 ? "已合并 \(groupedItems.count) 份" : medicine.displayStatus
    }

    private var relatedReminders: [ReminderPlan] {
        let owner = app.normalizedMemberName(medicine.owner)
        let appliesToAll = owner.isEmpty || app.isSharedMedicineOwner(owner)
        return app.reminders.filter { $0.medicineName == medicine.name && (appliesToAll || $0.memberName == owner) }
    }

    private var relatedRecords: [DoseRecord] {
        app.records.filter { $0.title.contains(medicine.name) }
    }

    var body: some View {
        ScrollPage(title: medicine.name, subtitle: "家庭药箱 / 药品详情", showBack: true, trailingSystemImage: "ellipsis") {
            HeroCard {
                Text("药品详情")
                    .font(.system(size: 20, weight: .heavy, design: .rounded))
                Text(detailSummary)
                    .font(.ybBody)
                    .opacity(0.92)

                HStack(spacing: 10) {
                    MetricTile(number: emptyText(displayStock), title: "剩余库存", tint: .ybPrimary)
                    MetricTile(number: emptyText(medicine.expiryDisplayText), title: "有效期", tint: .ybOrange)
                    MetricTile(number: emptyText(medicine.location), title: "位置", tint: .ybBlue)
                }
            }

            YBCard {
                SectionTitle(title: "基础信息", trailing: "可编辑")
                InfoRow(label: "所属成员", value: emptyText(medicine.owner))
                Divider()
                InfoRow(label: "药品分类", value: emptyText(medicine.category))
                Divider()
                InfoRow(label: "家中位置", value: emptyText(medicine.location))
                Divider()
                InfoRow(label: "生产日期", value: emptyText(medicine.productionDate))
                Divider()
                InfoRow(label: "保质期", value: emptyText(medicine.shelfLife))
                Divider()
                InfoRow(label: "到期日期", value: emptyText(medicine.expiry))
                Divider()
                InfoRow(label: "库存状态", value: displayStatus)
                if groupedItems.count > 1 {
                    Divider()
                    InfoRow(label: "合计库存", value: emptyText(displayStock))
                }

                PrimaryButton(title: "编辑药箱信息", systemImage: "pencil.circle.fill") {
                    showEditSheet = true
                }

                if shouldShowConfirmButton {
                    SecondaryButton(title: isConfirming ? "保存中..." : "信息已核对，标记正常", systemImage: "checkmark.shield.fill") {
                        Task { await confirmMedicineInfo() }
                    }
                    .disabled(isConfirming)
                }

                if !detailMessage.isEmpty {
                    Text(detailMessage)
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybPrimary)
                }
            }

            YBCard {
                HStack {
                    Text("用药卡片")
                        .font(.ybCardTitle)
                    Spacer()
                    Text("说明书整理")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybPrimary)
                        .fontWeight(.heavy)
                }
                InfoRow(label: "一次用量", value: emptyText(medicine.dose))
                Divider()
                InfoRow(label: "每日次数", value: emptyText(medicine.frequency))
                Divider()
                InfoRow(label: "服用时间", value: emptyText(medicine.mealTime))
                Divider()
                InfoRow(label: "服用方式", value: emptyText(medicine.method))
                Divider()
                Text("风险提示")
                    .font(.ybSubtitle)
                if medicine.risks.isEmpty {
                    Text("暂无风险标签，但仍需核对正式说明书。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                } else {
                    TagWrapView(tags: medicine.risks, tint: .ybOrange)
                }
                Text(emptyText(medicine.note))
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
            }

            YBCard {
                SectionTitle(title: "提醒计划", trailing: relatedReminders.isEmpty ? "未设置" : "共 \(relatedReminders.count) 条")
                if relatedReminders.isEmpty {
                    Text("当前药品还没有提醒计划。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                    PrimaryButton(title: "设置提醒", systemImage: "alarm.fill") {
                        app.pendingReminderMedicine = medicine
                        app.pendingReminderMember = (medicine.owner.isEmpty || app.isSharedMedicineOwner(medicine.owner)) ? nil : medicine.owner
                        app.path.append(Route.reminderSetting)
                    }
                } else {
                    ForEach(relatedReminders) { reminder in
                        ReminderRow(reminder: reminder)
                        Divider()
                    }
                }
            }

            YBCard {
                SectionTitle(title: "最近记录", trailing: relatedRecords.isEmpty ? "暂无" : "全部")
                if relatedRecords.isEmpty {
                    Text("还没有该药品的服药记录。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                } else {
                    ForEach(Array(relatedRecords.prefix(3)), id: \.id) { record in
                        HStack(spacing: 10) {
                            Text(record.status.contains("待") ? "…" : "✓")
                                .font(.system(size: 15, weight: .heavy))
                                .frame(width: 26, height: 26)
                                .background(record.status.contains("待") ? Color.ybOrange.opacity(0.12) : Color.ybGreen.opacity(0.12))
                                .foregroundStyle(record.status.contains("待") ? Color.ybOrange : Color.ybGreen)
                                .clipShape(Circle())
                            VStack(alignment: .leading, spacing: 3) {
                                Text(record.title)
                                    .font(.system(size: 14, weight: .heavy, design: .rounded))
                                Text(record.detail)
                                    .font(.ybCaption)
                                    .foregroundStyle(Color.ybMuted)
                            }
                            Spacer()
                        }
                        Divider()
                    }
                }
            }

            YBCard {
                SectionTitle(title: "药箱管理")
                Text(deleteDescription)
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
                PrimaryButton(title: isDeleting ? "删除中..." : deleteButtonTitle, systemImage: "trash.fill", color: .ybRed) {
                    showDeleteConfirm = true
                }
                .disabled(isDeleting)
            }

        }
        .sheet(isPresented: $showEditSheet) {
            MedicineSaveSheet(medicine: medicine, mode: .edit)
                .environmentObject(app)
        }
        .confirmationDialog(deleteConfirmTitle, isPresented: $showDeleteConfirm, titleVisibility: .visible) {
            Button("删除", role: .destructive) {
                Task { await deleteMedicine() }
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text(deleteConfirmMessage)
        }
        .refreshable {
            await app.refreshFromBackend()
        }
    }

    private var shouldShowConfirmButton: Bool {
        medicine.displayStatus.contains("确认") || medicine.displayStatus.contains("识别不完整")
    }

    private func confirmMedicineInfo() async {
        guard !isConfirming else { return }
        isConfirming = true
        detailMessage = ""
        defer { isConfirming = false }

        var updated = medicine
        updated.status = "正常"
        updated.needsConfirmation = false
        updated.fallbackFields = []
        updated.missingFields = []

        do {
            let saved = try await app.updateMedicine(updated)
            app.currentMedicine = saved
            detailMessage = "已标记为正常。"
        } catch {
            detailMessage = "保存失败，请确认后端正在运行。"
        }
    }

    private func deleteMedicine() async {
        isDeleting = true
        let medicinesToDelete = groupedItems
        for item in medicinesToDelete {
            await app.deleteMedicine(item)
        }
        isDeleting = false
        app.switchToTab(.box)
    }

    private var deleteButtonTitle: String {
        groupedItems.count > 1 ? "删除这组药品" : "删除这个药品"
    }

    private var deleteDescription: String {
        if groupedItems.count > 1 {
            return "这张卡片合并了 \(groupedItems.count) 份相同药品。删除后，这组药品会从家庭药箱中移除；相关提醒和今天的服药记录也会同步清理。"
        }
        return "删除后，该药品会从家庭药箱中移除；相关提醒和今天的服药记录也会同步清理。"
    }

    private var deleteConfirmTitle: String {
        groupedItems.count > 1 ? "确认删除这组药品？" : "确认删除这个药品？"
    }

    private var deleteConfirmMessage: String {
        groupedItems.count > 1 ? "删除后，药箱里这组已合并的药品都将不再显示。" : "删除后药箱里将不再显示这个药品。"
    }

    private var detailSummary: String {
        let owner = medicine.owner.isEmpty ? "未选择成员" : medicine.owner
        let location = medicine.location.isEmpty ? "未填写位置" : medicine.location
        return "\(owner) · \(medicine.category.isEmpty ? "未分类" : medicine.category) · 放在\(location)。"
    }

    private func emptyText(_ value: String) -> String {
        value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? "待填写" : value
    }
}
