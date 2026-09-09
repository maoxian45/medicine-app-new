import SwiftUI
import Combine

@MainActor
final class AppState: ObservableObject {
    @Published var selectedTab: AppTab = .home
    @Published var path = NavigationPath()
    @Published var medicines: [Medicine] = MockData.medicines
    @Published var members: [FamilyMember] = MockData.members
    @Published var reminders: [ReminderPlan] = MockData.reminders
    @Published var records: [DoseRecord] = MockData.records
    @Published var todayStatus: TodayStatus? = nil
    @Published var currentMedicine: Medicine = MockData.ibuprofen
    @Published var lastOCRText: String = ""
    @Published var pendingReminderMember: String? = nil
    @Published var pendingReminderMedicine: Medicine? = nil

    let speech = SpeechService.shared
    let notifications = NotificationService.shared

    var todayItems: [TodayMedicationItem] {
        if let todayStatus {
            return todayStatus.items
        }
        return reminders.enumerated().map { index, reminder in
            TodayMedicationItem(
                fallbackID: index,
                reminderBackendID: reminder.backendID,
                medicineName: reminder.medicineName,
                memberName: reminder.memberName,
                time: reminder.time,
                mealLabel: reminder.mealLabel,
                dose: reminder.dose,
                status: reminder.status.contains("已") ? "已服药" : "待服药",
                recordBackendID: nil,
                takenAt: nil
            )
        }
    }

    var todayTotal: Int { todayStatus?.total ?? reminders.count }
    var todayCompleted: Int { todayStatus?.completed ?? todayItems.filter(\.isCompleted).count }
    var todayPending: Int { todayStatus?.pending ?? max(todayTotal - todayCompleted, 0) }

    func normalizedMemberName(_ name: String) -> String {
        name.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    func isSameMember(_ lhs: String, _ rhs: String) -> Bool {
        normalizedMemberName(lhs) == normalizedMemberName(rhs)
    }

    func todayItems(for memberName: String) -> [TodayMedicationItem] {
        let normalized = normalizedMemberName(memberName)
        guard !normalized.isEmpty else { return [] }
        return todayItems.filter { isSameMember($0.memberName, normalized) }
    }

    func medicines(for memberName: String) -> [Medicine] {
        let normalized = normalizedMemberName(memberName)
        guard !normalized.isEmpty else { return [] }
        return medicines.filter { medicineIsAvailable($0, for: normalized) }
    }

    func canOperate(memberName: String, as currentMemberName: String) -> Bool {
        isSameMember(memberName, currentMemberName)
    }

    func isReservedSelfMember(_ name: String) -> Bool {
        normalizedMemberName(name) == "我"
    }

    func isSharedMedicineOwner(_ name: String) -> Bool {
        normalizedMemberName(name) == "全部人"
    }

    func medicineIsAvailable(_ medicine: Medicine, for memberName: String) -> Bool {
        let owner = normalizedMemberName(medicine.owner)
        let member = normalizedMemberName(memberName)
        return owner.isEmpty || isSharedMedicineOwner(owner) || isSameMember(owner, member)
    }

    func isEligibleElderMember(_ name: String) -> Bool {
        let normalized = normalizedMemberName(name)
        return !normalized.isEmpty && !isReservedSelfMember(normalized)
    }

    func todayItemsForElder(_ memberName: String) -> [TodayMedicationItem] {
        guard isEligibleElderMember(memberName) else { return [] }
        return todayItems(for: memberName)
    }

    func medicinesForElder(_ memberName: String) -> [Medicine] {
        guard isEligibleElderMember(memberName) else { return [] }
        return medicines(for: memberName)
    }

    func canElderOperate(memberName: String, as currentElderName: String) -> Bool {
        isEligibleElderMember(currentElderName) && isSameMember(memberName, currentElderName)
    }

    func markTakenForElder(item: TodayMedicationItem, currentElderName: String) {
        guard canElderOperate(memberName: item.memberName, as: currentElderName) else {
            print("Blocked elder confirmation for \(item.memberName); current elder is \(currentElderName)")
            return
        }
        markTaken(item: item, allowStockFallback: false)
    }

    func cancelTakenForElder(item: TodayMedicationItem, currentElderName: String) {
        guard canElderOperate(memberName: item.memberName, as: currentElderName) else {
            print("Blocked elder cancellation for \(item.memberName); current elder is \(currentElderName)")
            return
        }
        cancelTaken(item: item, allowStockFallback: false)
    }

    var riskCount: Int {
        medicines.filter { medicine in
            medicine.status.contains("过期")
                || medicine.status.contains("少")
                || medicine.needsAttention
        }.count
    }

    /// 用于从任意详情页回到某个底部标签页。
    /// 先清空导航路径，避免目标页面仍被详情页盖住，从而看不到底部栏。
    func switchToTab(_ tab: AppTab) {
        path = NavigationPath()
        selectedTab = tab
    }

    func refreshFromBackend() async {
        do {
            let backendMembers = try await BackendClient.shared.fetchMembers()
            let backendMedicines = try await BackendClient.shared.fetchMedicines()
            let backendReminders = try await BackendClient.shared.fetchReminders()
            let backendRecords = try await BackendClient.shared.fetchRecords()
            let backendToday = try await BackendClient.shared.fetchTodayStatus()

            // fetch 成功时，空数组也是后端的真实状态；否则删除到最后一位成员后会被旧本地数据回填。
            members = backendMembers
            medicines = backendMedicines
            reminders = backendReminders
            records = backendRecords
            todayStatus = backendToday
        } catch {
            // 面向用户的页面不展示“后端是否连接”。联调排错时看 Xcode/VSCode 控制台即可。
            print("Backend sync failed: \(error.localizedDescription)")
        }
    }

    func refreshRecords(
        memberID: Int?,
        medicineID: Int?,
        startDate: String?,
        endDate: String?
    ) async {
        do {
            records = try await BackendClient.shared.fetchRecords(
                memberID: memberID,
                medicineID: medicineID,
                startDate: startDate,
                endDate: endDate
            )
        } catch {
            print("Record sync failed: \(error.localizedDescription)")
        }
    }

    func saveMember(_ member: FamilyMember) async throws -> FamilyMember {
        var memberToSave = member
        memberToSave.name = memberToSave.name.trimmingCharacters(in: .whitespacesAndNewlines)
        memberToSave.role = memberToSave.role.trimmingCharacters(in: .whitespacesAndNewlines)
        memberToSave.age = memberToSave.age.trimmingCharacters(in: .whitespacesAndNewlines)
        memberToSave.weight = memberToSave.weight.trimmingCharacters(in: .whitespacesAndNewlines)
        memberToSave.allergy = memberToSave.allergy.trimmingCharacters(in: .whitespacesAndNewlines)
        if memberToSave.emoji.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            memberToSave.emoji = "🙂"
        }
        if memberToSave.role.isEmpty {
            memberToSave.role = "家庭成员"
        }
        memberToSave.status = ""

        if let index = members.firstIndex(where: {
            $0.name.trimmingCharacters(in: .whitespacesAndNewlines) == memberToSave.name
        }) {
            members[index] = memberToSave
            return memberToSave
        }

        let saved = try await BackendClient.shared.saveMember(memberToSave)
        if let backendID = saved.backendID,
           let index = members.firstIndex(where: { $0.backendID == backendID }) {
            members[index] = saved
        } else {
            members.append(saved)
        }
        await refreshFromBackend()
        return saved
    }

    func deleteMember(_ member: FamilyMember) async {
        members.removeAll { candidate in
            if let backendID = member.backendID { return candidate.backendID == backendID }
            return candidate.id == member.id
        }

        do {
            try await BackendClient.shared.deleteMember(member)
            await refreshFromBackend()
        } catch {
            print("Delete member failed: \(error.localizedDescription)")
        }
    }

    func saveMedicine(_ medicine: Medicine) async throws -> Medicine {
        var medicineToSave = medicine
        if medicineToSave.status == "待核对" || medicineToSave.status == "待确认" {
            medicineToSave.status = "需确认"
        }

        if let existing = medicines.first(where: {
            $0.backendID != medicineToSave.backendID
                && $0.groupingKey == medicineToSave.groupingKey
        }) {
            var merged = existing
            merged.stock = Medicine.mergedStocks([existing.stock, medicineToSave.stock])
            merged.expiry = medicineToSave.expiry.isEmpty ? existing.expiry : medicineToSave.expiry
            merged.productionDate = medicineToSave.productionDate.isEmpty ? existing.productionDate : medicineToSave.productionDate
            merged.shelfLife = medicineToSave.shelfLife.isEmpty ? existing.shelfLife : medicineToSave.shelfLife
            merged.dose = medicineToSave.dose.isEmpty ? existing.dose : medicineToSave.dose
            merged.frequency = medicineToSave.frequency.isEmpty ? existing.frequency : medicineToSave.frequency
            merged.mealTime = medicineToSave.mealTime.isEmpty ? existing.mealTime : medicineToSave.mealTime
            merged.method = medicineToSave.method.isEmpty ? existing.method : medicineToSave.method
            merged.note = medicineToSave.note.isEmpty ? existing.note : medicineToSave.note
            merged.status = medicineToSave.status

            let saved = try await updateMedicine(merged)
            return saved
        }

        let saved = try await BackendClient.shared.saveMedicine(medicineToSave)
        if let backendID = saved.backendID,
           let index = medicines.firstIndex(where: { $0.backendID == backendID }) {
            medicines[index] = saved
        } else if !medicines.contains(where: { $0.groupingKey == saved.groupingKey }) {
            medicines.insert(saved, at: 0)
        }
        await refreshFromBackend()
        return saved
    }

    func updateMedicine(_ medicine: Medicine) async throws -> Medicine {
        if let backendID = medicine.backendID {
            let saved = try await BackendClient.shared.updateMedicine(medicine)
            if let index = medicines.firstIndex(where: { $0.backendID == backendID }) {
                medicines[index] = saved
            }
            await refreshFromBackend()
            return saved
        }

        if let index = medicines.firstIndex(where: { $0.id == medicine.id }) {
            medicines[index] = medicine
        }
        return medicine
    }

    func deleteMedicine(_ medicine: Medicine) async {
        medicines.removeAll { $0.id == medicine.id || ($0.backendID != nil && $0.backendID == medicine.backendID) }
        let owner = normalizedMemberName(medicine.owner)
        let appliesToAll = owner.isEmpty || isSharedMedicineOwner(owner)
        let reminderMatches: (ReminderPlan) -> Bool = { reminder in
            if let medicineID = medicine.backendID {
                return reminder.medicineBackendID == medicineID
            }
            return reminder.medicineName == medicine.name && (appliesToAll || reminder.memberName == owner)
        }
        let recordMatches: (DoseRecord) -> Bool = { record in
            if let medicineID = medicine.backendID {
                return record.medicineBackendID == medicineID
            }
            return record.title.contains(medicine.name) && (appliesToAll || record.title.contains(owner))
        }
        let remindersToRemove = reminders.filter(reminderMatches)
        remindersToRemove.forEach {
            notifications.cancelDailyReminder(medicineName: $0.medicineName, memberName: $0.memberName, time: $0.time)
        }
        reminders.removeAll(where: reminderMatches)
        records.removeAll(where: recordMatches)

        do {
            try await BackendClient.shared.deleteMedicine(medicine)
            await refreshFromBackend()
        } catch {
            print("Delete medicine failed: \(error.localizedDescription)")
        }
    }

    func saveReminder(_ reminder: ReminderPlan) async throws -> ReminderPlan {
        let saved = try await BackendClient.shared.saveReminder(reminder)
        reminders.append(saved)
        await refreshFromBackend()
        return saved
    }

    func deleteReminder(_ reminder: ReminderPlan) async {
        notifications.cancelDailyReminder(medicineName: reminder.medicineName, memberName: reminder.memberName, time: reminder.time)

        reminders.removeAll { candidate in
            if let backendID = reminder.backendID { return candidate.backendID == backendID }
            return candidate.id == reminder.id
        }

        records.removeAll { record in
            if let backendID = reminder.backendID { return record.reminderBackendID == backendID }
            return record.title.contains(reminder.medicineName) && record.title.contains(reminder.memberName)
        }

        if var snapshot = todayStatus {
            snapshot.items.removeAll { item in
                if let backendID = reminder.backendID { return item.reminderBackendID == backendID }
                return item.medicineName == reminder.medicineName
                    && item.memberName == reminder.memberName
                    && item.time == reminder.time
            }
            snapshot.total = snapshot.items.count
            snapshot.completed = snapshot.items.filter(\.isCompleted).count
            snapshot.pending = max(snapshot.total - snapshot.completed, 0)
            todayStatus = snapshot
        }

        do {
            try await BackendClient.shared.deleteReminder(reminder)
            await refreshFromBackend()
        } catch {
            print("Delete reminder failed: \(error.localizedDescription)")
        }
    }

    func recordChildFeeding(
        medicine: Medicine,
        member: FamilyMember,
        recordedBy: String,
        temperature: String,
        note: String
    ) async throws {
        guard let medicineID = medicine.backendID, let memberID = member.backendID else {
            throw URLError(.badURL)
        }
        let saved = try await BackendClient.shared.markTaken(
            medicineID: medicineID,
            memberID: memberID,
            medicineName: medicine.name,
            memberName: member.name,
            dose: medicine.dose,
            recordedBy: recordedBy,
            temperature: temperature,
            note: note
        )
        records.removeAll { $0.backendID == saved.backendID }
        records.insert(saved, at: 0)

        let adjusted = adjustLocalStock(
            medicineName: medicine.name,
            memberName: member.name,
            dose: medicine.dose,
            direction: -1
        )
        if let adjusted, adjusted.backendID != nil {
            _ = try await BackendClient.shared.updateMedicine(adjusted)
        }
        await refreshFromBackend()
    }

    func markTaken(reminder: ReminderPlan) {
        if let item = todayItems.first(where: { matches(reminder: reminder, item: $0) }), item.isCompleted {
            return
        }

        markTaken(
            reminderID: reminder.backendID,
            medicineName: reminder.medicineName,
            memberName: reminder.memberName,
            dose: reminder.dose
        )
    }

    func markTaken(item: TodayMedicationItem, allowStockFallback: Bool = true) {
        guard !item.isCompleted else { return }
        markTaken(
            reminderID: item.reminderBackendID,
            medicineName: item.medicineName,
            memberName: item.memberName,
            dose: item.dose,
            allowStockFallback: allowStockFallback
        )
    }

    func markTaken(reminderID: Int? = nil, medicineName: String, memberName: String = "我", dose: String = "", allowStockFallback: Bool = true) {
        if let reminderID, todayItems.first(where: { $0.reminderBackendID == reminderID })?.isCompleted == true {
            return
        }

        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        let time = formatter.string(from: Date())

        records.insert(
            DoseRecord(
                reminderBackendID: reminderID,
                time: time,
                title: "\(medicineName) · \(memberName)",
                detail: "已服药 · \(dose.isEmpty ? "已确认" : dose)",
                status: "已服药"
            ),
            at: 0
        )

        if let reminderID,
           let index = reminders.firstIndex(where: { $0.backendID == reminderID }) {
            reminders[index].status = "已服药"
        }

        if var snapshot = todayStatus,
           let reminderID,
           let itemIndex = snapshot.items.firstIndex(where: { $0.reminderBackendID == reminderID }),
           !snapshot.items[itemIndex].isCompleted {
            snapshot.items[itemIndex].status = "已服药"
            snapshot.items[itemIndex].takenAt = time
            snapshot.completed = min(snapshot.total, snapshot.completed + 1)
            snapshot.pending = max(snapshot.total - snapshot.completed, 0)
            todayStatus = snapshot
        }

        let adjustedMedicine = adjustLocalStock(medicineName: medicineName, memberName: memberName, dose: dose, direction: -1, allowFallback: allowStockFallback)

        Task {
            do {
                _ = try await BackendClient.shared.markTaken(
                    reminderID: reminderID,
                    medicineName: medicineName,
                    memberName: memberName,
                    dose: dose
                )
                if let adjustedMedicine, adjustedMedicine.backendID != nil {
                    _ = try await BackendClient.shared.updateMedicine(adjustedMedicine)
                }
                await refreshFromBackend()
            } catch {
                print("Mark taken failed: \(error.localizedDescription)")
            }
        }
    }

    func cancelTaken(reminder: ReminderPlan) {
        guard let item = todayItems.first(where: { matches(reminder: reminder, item: $0) }) else { return }
        cancelTaken(item: item)
    }

    func cancelTaken(record: DoseRecord) {
        let parsed = parseRecord(record)
        removeRecordLocally(recordBackendID: record.backendID, reminderID: record.reminderBackendID)
        let adjustedMedicine = adjustLocalStock(medicineName: parsed.medicineName, memberName: parsed.memberName, dose: parsed.dose, direction: 1)

        Task {
            do {
                try await BackendClient.shared.deleteRecord(record)
                if let adjustedMedicine, adjustedMedicine.backendID != nil {
                    _ = try await BackendClient.shared.updateMedicine(adjustedMedicine)
                }
                await refreshFromBackend()
            } catch {
                print("Cancel taken failed: \(error.localizedDescription)")
            }
        }
    }

    func cancelTaken(item: TodayMedicationItem, allowStockFallback: Bool = true) {
        guard item.isCompleted else { return }
        removeRecordLocally(recordBackendID: item.recordBackendID, reminderID: item.reminderBackendID)

        if let reminderID = item.reminderBackendID,
           let index = reminders.firstIndex(where: { $0.backendID == reminderID }) {
            reminders[index].status = "待服药"
        }

        if var snapshot = todayStatus,
           let reminderID = item.reminderBackendID,
           let itemIndex = snapshot.items.firstIndex(where: { $0.reminderBackendID == reminderID }),
           snapshot.items[itemIndex].isCompleted {
            snapshot.items[itemIndex].status = "待服药"
            snapshot.items[itemIndex].recordBackendID = nil
            snapshot.items[itemIndex].takenAt = nil
            snapshot.completed = max(snapshot.completed - 1, 0)
            snapshot.pending = max(snapshot.total - snapshot.completed, 0)
            todayStatus = snapshot
        }

        let adjustedMedicine = adjustLocalStock(medicineName: item.medicineName, memberName: item.memberName, dose: item.dose, direction: 1, allowFallback: allowStockFallback)

        Task {
            do {
                try await BackendClient.shared.deleteRecord(recordID: item.recordBackendID)
                if let adjustedMedicine, adjustedMedicine.backendID != nil {
                    _ = try await BackendClient.shared.updateMedicine(adjustedMedicine)
                }
                await refreshFromBackend()
            } catch {
                print("Cancel taken failed: \(error.localizedDescription)")
            }
        }
    }

    private func matches(reminder: ReminderPlan, item: TodayMedicationItem) -> Bool {
        if let reminderID = reminder.backendID, item.reminderBackendID == reminderID { return true }
        return reminder.medicineName == item.medicineName
            && reminder.memberName == item.memberName
            && reminder.time == item.time
    }

    private func removeRecordLocally(recordBackendID: Int?, reminderID: Int?) {
        if let recordBackendID {
            records.removeAll { $0.backendID == recordBackendID }
        } else if let reminderID {
            records.removeAll { $0.reminderBackendID == reminderID }
        }
    }

    private func parseRecord(_ record: DoseRecord) -> (medicineName: String, memberName: String, dose: String) {
        let titleParts = record.title.components(separatedBy: "·").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
        let detailParts = record.detail.components(separatedBy: "·").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
        return (
            medicineName: titleParts.first ?? record.title,
            memberName: titleParts.count > 1 ? titleParts[1] : "我",
            dose: detailParts.count > 1 ? detailParts[1] : ""
        )
    }

    private func adjustLocalStock(medicineName: String, memberName: String, dose: String, direction: Double, allowFallback: Bool = true) -> Medicine? {
        let normalizedName = Medicine.normalized(medicineName)
        let doseQuantity = Medicine.doseQuantity(from: dose)
        guard doseQuantity > 0 else { return nil }

        let ownerMatchedIndex = medicines.firstIndex { medicine in
            Medicine.normalized(medicine.name) == normalizedName
                && isSameMember(medicine.owner, memberName)
                && medicine.stockAmount != nil
        }

        let sharedMatchedIndex = medicines.firstIndex { medicine in
            Medicine.normalized(medicine.name) == normalizedName
                && isSharedMedicineOwner(medicine.owner)
                && medicine.stockAmount != nil
        }

        let fallbackIndex = allowFallback ? medicines.firstIndex { medicine in
            Medicine.normalized(medicine.name) == normalizedName
                && medicine.stockAmount != nil
        } : nil

        guard let index = ownerMatchedIndex ?? sharedMatchedIndex ?? fallbackIndex else { return nil }

        medicines[index].stock = medicines[index].adjustedStock(by: direction * doseQuantity)
        if let amount = medicines[index].stockAmount, amount.quantity <= 3 {
            medicines[index].status = "库存不足"
        } else if medicines[index].displayStatus.contains("库存不足") {
            medicines[index].status = "正常"
        }
        return medicines[index]
    }

    func speakCurrentMedicine() {
        if !currentMedicine.speechText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            speech.speak(currentMedicine.speechText)
            return
        }
        let text = "\(currentMedicine.name)，一次用量 \(currentMedicine.dose)，每日 \(currentMedicine.frequency)，\(currentMedicine.mealTime)服用。\(currentMedicine.note) 用药请以医生、药师建议及正式说明书为准。"
        speech.speak(text)
    }
}
