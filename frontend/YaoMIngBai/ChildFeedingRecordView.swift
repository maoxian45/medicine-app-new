import SwiftUI

struct ChildFeedingRecordView: View {
    @EnvironmentObject private var app: AppState

    let memberName: String

    @State private var selectedMedicineKey = ""
    @State private var showRecordConfirmation = false
    @State private var feedbackMessage = ""
    @State private var recordedBy = ""
    @State private var temperature = ""
    @State private var note = ""
    @State private var isSaving = false

    private var member: FamilyMember? {
        app.members.first { app.isSameMember($0.name, memberName) }
    }

    private var memberAge: String {
        let value = member?.age.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return value.isEmpty ? "未填写" : value
    }

    private var memberWeight: String {
        let value = member?.weight.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return value.isEmpty ? "未填写" : value
    }

    private var medicineOptions: [Medicine] {
        app.medicines(for: memberName)
            .filter { !$0.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
    }

    private var selectedMedicine: Medicine? {
        medicineOptions.first { medicineKey($0) == selectedMedicineKey }
            ?? medicineOptions.first
    }

    private var matchingRecords: [DoseRecord] {
        app.records.filter { record in
            if let memberID = member?.backendID, let recordMemberID = record.memberBackendID {
                guard memberID == recordMemberID else { return false }
            } else {
                guard record.title.contains(memberName) else { return false }
            }
            guard let selectedMedicine else { return true }
            if let medicineID = selectedMedicine.backendID, let recordMedicineID = record.medicineBackendID {
                return medicineID == recordMedicineID
            }
            return record.title.contains(selectedMedicine.name)
        }
    }

    private var latestRecord: DoseRecord? {
        matchingRecords.first
    }

    private var latestRecordSummary: String {
        guard let latestRecord else { return "还没有喂药记录" }
        if latestRecord.time == "现在" { return "刚刚已记录" }
        return "上次记录于 \(latestRecord.time)"
    }

    var body: some View {
        ScrollPage(
            title: "儿童喂药记录",
            subtitle: "家庭成员 / \(memberName)",
            showBack: true,
            trailingSystemImage: "ellipsis"
        ) {
            HeroCard {
                Text(latestRecordSummary)
                    .font(.system(size: 22, weight: .heavy, design: .rounded))
                Text("记录用于帮助多位照护者核对上次喂药情况；是否再次用药仍需以医生、药师建议或正式说明书为准。")
                    .font(.ybBody)
                    .opacity(0.92)

                HStack(spacing: 10) {
                    MetricTile(number: memberAge, title: "年龄", tint: .ybPrimary)
                    MetricTile(number: memberWeight, title: "体重", tint: .ybBlue)
                    MetricTile(number: "\(matchingRecords.count)", title: "今日记录", tint: .ybOrange)
                }
            }

            YBCard {
                SectionTitle(title: "选择药品", trailing: selectedMedicine == nil ? "请先添加" : "家庭药箱")

                if medicineOptions.isEmpty {
                    Text("还没有给 \(memberName) 添加可用药品。请先把药品加入家庭药箱，并将使用者选择为 \(memberName) 或全部人。")
                        .font(.ybBody)
                        .foregroundStyle(Color.ybMuted)
                    SecondaryButton(title: "先添加药品", systemImage: "plus.circle.fill") {
                        app.path.append(Route.addMedicine)
                    }
                } else {
                    Picker("当前药品", selection: $selectedMedicineKey) {
                        ForEach(medicineOptions) { medicine in
                            Text(medicine.name)
                                .tag(medicineKey(medicine))
                        }
                    }
                    .pickerStyle(.menu)
                    .frame(maxWidth: .infinity, alignment: .leading)

                    if let medicine = selectedMedicine {
                        HStack(spacing: 12) {
                            EmojiCircle(emoji: medicine.emoji, size: 50)
                            VStack(alignment: .leading, spacing: 4) {
                                Text(medicine.name)
                                    .font(.system(size: 17, weight: .heavy, design: .rounded))
                                Text("\(medicine.category.isEmpty ? "药品" : medicine.category) · \(medicine.dose.isEmpty ? "剂量待核对" : medicine.dose)")
                                    .font(.ybCaption)
                                    .foregroundStyle(Color.ybMuted)
                            }
                        }
                    }
                }
            }

            YBCard {
                SectionTitle(title: "本次记录信息", trailing: "均可选")
                FormTextField(title: "记录人", placeholder: "例如：妈妈", text: $recordedBy)
                FormTextField(title: "体温", placeholder: "例如：37.2℃", text: $temperature)
                FormTextField(title: "备注", placeholder: "例如：饭后服用", text: $note)
            }

            YBCard {
                HStack(alignment: .top, spacing: 10) {
                    EmojiCircle(emoji: "⚠️", size: 40, background: Color.ybOrange.opacity(0.12))
                    VStack(alignment: .leading, spacing: 4) {
                        Text("记录前先核对")
                            .font(.system(size: 15, weight: .heavy, design: .rounded))
                        Text(latestRecord.map { "最近一条：\($0.time) · \($0.detail)。请确认不是其他照护者刚刚记录过。" } ?? "当前没有找到今日记录，仍请核对实际喂药情况。")
                            .font(.ybCaption)
                            .foregroundStyle(Color.ybMuted)
                    }
                }
            }

            YBCard {
                SectionTitle(title: "今日喂药时间轴", trailing: "共 \(matchingRecords.count) 条")
                if matchingRecords.isEmpty {
                    Text("今天还没有为该药品保存喂药记录。")
                        .font(.ybCaption)
                        .foregroundStyle(Color.ybMuted)
                } else {
                    ForEach(Array(matchingRecords.prefix(10))) { record in
                        TimelineRow(time: record.time, title: record.title, detail: record.detail)
                        Divider()
                    }
                }
            }

            if !feedbackMessage.isEmpty {
                Text(feedbackMessage)
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybPrimary)
                    .frame(maxWidth: .infinity, alignment: .center)
            }

            HStack(spacing: 10) {
                PrimaryButton(title: "记录已喂药", systemImage: "plus.circle.fill") {
                    showRecordConfirmation = true
                }
                .disabled(selectedMedicine == nil || isSaving)
                .opacity(selectedMedicine == nil || isSaving ? 0.45 : 1)

                SecondaryButton(title: "设置下次提醒", systemImage: "bell.fill") {
                    openReminderSetting()
                }
                .disabled(selectedMedicine == nil)
                .opacity(selectedMedicine == nil ? 0.45 : 1)
            }
        }
        .onAppear(perform: ensureSelectedMedicine)
        .onChange(of: medicineOptions.map(\.id)) { _ in
            ensureSelectedMedicine()
        }
        .task(id: selectedMedicineKey) {
            await loadTodayRecords()
        }
        .confirmationDialog(
            "确认记录已喂药？",
            isPresented: $showRecordConfirmation,
            titleVisibility: .visible
        ) {
            Button("确认记录") {
                recordFeeding()
            }
            Button("取消", role: .cancel) {}
        } message: {
            if let medicine = selectedMedicine {
                Text("\(memberName) · \(medicine.name) · \(medicine.dose.isEmpty ? "剂量待核对" : medicine.dose)。保存前请确认没有重复喂药。")
            }
        }
    }

    private func ensureSelectedMedicine() {
        guard let first = medicineOptions.first else {
            selectedMedicineKey = ""
            return
        }
        if !medicineOptions.contains(where: { medicineKey($0) == selectedMedicineKey }) {
            selectedMedicineKey = medicineKey(first)
        }
    }

    private func recordFeeding() {
        guard let medicine = selectedMedicine, let member else { return }
        isSaving = true
        feedbackMessage = ""
        Task {
            defer { isSaving = false }
            do {
                try await app.recordChildFeeding(
                    medicine: medicine,
                    member: member,
                    recordedBy: recordedBy.trimmingCharacters(in: .whitespacesAndNewlines),
                    temperature: temperature.trimmingCharacters(in: .whitespacesAndNewlines),
                    note: note.trimmingCharacters(in: .whitespacesAndNewlines)
                )
                await loadTodayRecords()
                feedbackMessage = "已记录 \(memberName) 服用 \(medicine.name)。"
                note = ""
            } catch {
                feedbackMessage = "保存失败，请确认药品和成员已同步到后端后重试。"
            }
        }
    }

    private func loadTodayRecords() async {
        guard let memberID = member?.backendID,
              let medicineID = selectedMedicine?.backendID else { return }
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let today = formatter.string(from: Date())
        await app.refreshRecords(
            memberID: memberID,
            medicineID: medicineID,
            startDate: today,
            endDate: today
        )
    }

    private func openReminderSetting() {
        guard let medicine = selectedMedicine else { return }
        app.pendingReminderMember = memberName
        app.pendingReminderMedicine = medicine
        app.path.append(Route.reminderSetting)
    }

    private func medicineKey(_ medicine: Medicine) -> String {
        if let backendID = medicine.backendID { return "backend-\(backendID)" }
        return medicine.id.uuidString
    }
}

struct TimelineRow: View {
    var time: String
    var title: String
    var detail: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text(time)
                .font(.system(size: 13, weight: .heavy, design: .rounded))
                .foregroundStyle(Color.ybPrimary)
                .frame(width: 52, alignment: .leading)
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 14, weight: .heavy, design: .rounded))
                Text(detail)
                    .font(.ybCaption)
                    .foregroundStyle(Color.ybMuted)
            }
            Spacer()
        }
        .padding(.vertical, 8)
    }
}
