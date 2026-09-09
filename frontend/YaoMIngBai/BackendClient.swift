import Foundation

/// 所有 FastAPI 请求集中在这里。这个文件只给开发者使用，不在 App 页面里暴露“后端连接状态”。
/// 模拟器连接同一台 Mac 上的后端时使用 http://127.0.0.1:8000。
/// 真机联调时把这里改成 Mac 的局域网 IP，例如 http://192.168.1.23:8000。
final class BackendClient {
    static let shared = BackendClient()

    var baseURL = URL(string: "http://127.0.0.1:8000")!

    private let session: URLSession

    private init(session: URLSession = .shared) {
        self.session = session
    }

    func checkHealth() async throws -> Bool {
        let health: HealthResponse = try await get("/api/health")
        return health.status == "ok"
    }

    func parseInstructionText(
    _ text: String
) async throws -> Medicine {
    let trimmedText = text.trimmingCharacters(
        in: .whitespacesAndNewlines
    )

    guard !trimmedText.isEmpty else {
        throw URLError(.zeroByteResource)
    }

    let response: InstructionResponse = try await post(
        "/api/instruction/parse",
        body: InstructionParsePayload(
            ocrText: trimmedText
        )
    )

    return response.toMedicine(
        originalTextOverride: trimmedText
    )
}

    private func fallbackMedicineName(from text: String) -> String {
        let firstLine = text
            .split(whereSeparator: \.isNewline)
            .map { String($0).trimmingCharacters(in: .whitespacesAndNewlines) }
            .first { !$0.isEmpty }

        guard let firstLine else { return "待核对药品" }
        return firstLine.count > 30 ? String(firstLine.prefix(30)) : firstLine
    }

    func fetchMembers() async throws -> [FamilyMember] {
        let response: [MemberResponse] = try await get("/api/members")
        return response.map { $0.toMember() }
    }

    func saveMember(_ member: FamilyMember) async throws -> FamilyMember {
        let response: MemberResponse = try await post(
            "/api/members",
            body: MemberPayload(from: member)
        )
        return response.toMember()
    }

    func deleteMember(_ member: FamilyMember) async throws {
        guard let backendID = member.backendID else { return }
        try await delete("/api/members/\(backendID)")
    }

    func fetchMedicines() async throws -> [Medicine] {
        let response: [MedicineResponse] = try await get("/api/medicines")
        return response.map { $0.toMedicine() }
    }

    func saveMedicine(_ medicine: Medicine) async throws -> Medicine {
        let response: MedicineResponse = try await post(
            "/api/medicines",
            body: MedicinePayload(from: medicine)
        )
        return response.toMedicine()
    }

    func updateMedicine(_ medicine: Medicine) async throws -> Medicine {
        guard let backendID = medicine.backendID else { return medicine }
        let response: MedicineResponse = try await put(
            "/api/medicines/\(backendID)",
            body: MedicinePayload(from: medicine)
        )
        return response.toMedicine()
    }

    func deleteMedicine(_ medicine: Medicine) async throws {
        guard let backendID = medicine.backendID else { return }
        try await delete("/api/medicines/\(backendID)")
    }

    func fetchReminders() async throws -> [ReminderPlan] {
        let response: [ReminderResponse] = try await get("/api/reminders")
        return response.map { $0.toReminder() }
    }

    func saveReminder(_ reminder: ReminderPlan) async throws -> ReminderPlan {
        guard reminder.medicineBackendID != nil else {
            throw URLError(.badURL)
        }
        let response: ReminderResponse = try await post(
            "/api/reminders",
            body: ReminderPayload(from: reminder)
        )
        return response.toReminder()
    }

    func deleteReminder(_ reminder: ReminderPlan) async throws {
        guard let backendID = reminder.backendID else { return }
        try await delete("/api/reminders/\(backendID)")
    }

    func fetchRecords(
        memberID: Int? = nil,
        medicineID: Int? = nil,
        startDate: String? = nil,
        endDate: String? = nil
    ) async throws -> [DoseRecord] {
        var queryItems: [URLQueryItem] = []
        if let memberID { queryItems.append(URLQueryItem(name: "member_id", value: String(memberID))) }
        if let medicineID { queryItems.append(URLQueryItem(name: "medicine_id", value: String(medicineID))) }
        if let startDate { queryItems.append(URLQueryItem(name: "start_date", value: startDate)) }
        if let endDate { queryItems.append(URLQueryItem(name: "end_date", value: endDate)) }

        let response: [RecordResponse] = try await get("/api/records", queryItems: queryItems)
        return response.map { $0.toRecord() }
    }

    func markTaken(
        reminderID: Int? = nil,
        medicineID: Int? = nil,
        memberID: Int? = nil,
        medicineName: String,
        memberName: String,
        dose: String,
        recordedBy: String = "",
        temperature: String = "",
        note: String = ""
    ) async throws -> DoseRecord {
        let response: RecordResponse = try await post(
            "/api/records",
            body: RecordPayload(
                reminderId: reminderID,
                medicineId: medicineID,
                memberId: memberID,
                medicineName: medicineName,
                memberName: memberName,
                dose: dose,
                recordedBy: recordedBy,
                temperature: temperature,
                note: note,
                status: "已服药"
            )
        )
        return response.toRecord()
    }

    func deleteRecord(recordID: Int?) async throws {
        guard let recordID else { return }
        try await delete("/api/records/\(recordID)")
    }

    func deleteRecord(_ record: DoseRecord) async throws {
        try await deleteRecord(recordID: record.backendID)
    }

    func fetchTodayStatus() async throws -> TodayStatus {
        let response: TodayResponse = try await get("/api/today")
        return response.toTodayStatus()
    }

    private func get<Response: Decodable>(_ path: String, queryItems: [URLQueryItem] = []) async throws -> Response {
        var url = makeURL(path)
        if !queryItems.isEmpty {
            var components = URLComponents(url: url, resolvingAgainstBaseURL: true)!
            components.queryItems = queryItems
            url = components.url!
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        return try await send(request)
    }

    private func post<Response: Decodable, Body: Encodable>(_ path: String, body: Body) async throws -> Response {
        var request = URLRequest(url: makeURL(path))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try Self.encoder.encode(body)
        return try await send(request)
    }

    private func put<Response: Decodable, Body: Encodable>(_ path: String, body: Body) async throws -> Response {
        var request = URLRequest(url: makeURL(path))
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try Self.encoder.encode(body)
        return try await send(request)
    }

    private func delete(_ path: String) async throws {
        var request = URLRequest(url: makeURL(path))
        request.httpMethod = "DELETE"
        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw URLError(.badServerResponse)
        }
    }

    private func makeURL(_ path: String) -> URL {
        URL(string: path, relativeTo: baseURL)!.absoluteURL
    }

    private func send<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        let (data, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try Self.decoder.decode(Response.self, from: data)
    }

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    private static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }()
}

private struct HealthResponse: Decodable {
    var status: String
}

private struct InstructionParsePayload: Encodable {
    var ocrText: String
}

private struct InstructionResponse: Decodable {
    // 后端解析接口的核心字段：严格兼容后端给出的字段，其他演示字段全部可选。
    var name: String?
    var spec: String?
    var dose: String?
    var frequency: String?
    var mealTime: String?
    var method: String?
    /// 后端这里的 location 是说明书里的“贮藏方式”，不是家中真实存放位置。
    var location: String?
    var expiry: String?
    var expiryText: String?
    var productionDate: String?
    var shelfLife: String?
    var risks: [String]?
    var contraindications: [String]?
    var precautions: [String]?
    var speechText: String?
    var elderSpeechText: String?
    var usedSampleFallback: Bool?
    var fallbackFields: [String]?
    var needsConfirmation: Bool?

    // 兼容当前后端/Mock 中可能额外返回的字段，全部设为可选，避免缺字段导致解析失败。
    var emoji: String?
    var category: String?
    var owner: String?
    var stock: String?
    var status: String?
    var note: String?
    var originalText: String?
    var demoOnly: Bool?
    var dataSource: String?
    var parseQuality: String?
    var missingFields: [String]?

    func toMedicine(originalTextOverride: String) -> Medicine {
        let parsedContraindications = contraindications ?? []
        let parsedPrecautions = precautions ?? []
        let cautionParts = (parsedContraindications + parsedPrecautions).filter { !$0.isEmpty }

        let combinedNote: String
        if let note, !note.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            combinedNote = note
        } else if !cautionParts.isEmpty {
            combinedNote = cautionParts.joined(separator: "\n")
        } else {
            combinedNote = "请核对药品包装、正式说明书或医生药师建议后再使用。"
        }

        let parsedNeedsConfirmation = needsConfirmation ?? true
        let parsedUsedSampleFallback = usedSampleFallback ?? false
        let parsedDemoOnly = demoOnly ?? false
        let parsedQuality = parseQuality ?? "partial"
        let parsedMissingFields = missingFields ?? []
        let finalStatus: String

        if parsedQuality == "poor" {
            finalStatus = "识别不完整"
        } else if parsedQuality == "partial" {
            finalStatus = "需确认"
        } else if let status,
                !status.trimmingCharacters(
                in: .whitespacesAndNewlines
                ).isEmpty {
            finalStatus = status
        } else if parsedNeedsConfirmation {
            finalStatus = "需确认"
        } else {
            finalStatus = "正常"
        }
        
        
        
        

        let rawExpiry = (expiry ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let parsedShelfLife = Self.looksLikeShelfLifeDuration(rawExpiry) ? rawExpiry : (shelfLife ?? "")
        let parsedExpiryDate = parsedShelfLife.isEmpty ? rawExpiry : ""

        return Medicine(
            emoji: emoji ?? "💊",
            name: (name ?? "").isEmpty ? "待确认药品" : (name ?? ""),
            spec: spec ?? "",
            category: category ?? "其他",
            owner: owner ?? "",
            dose: dose ?? "",
            frequency: frequency ?? "",
            mealTime: mealTime ?? "",
            method: method ?? "",
            location: location ?? "",
            productionDate: productionDate ?? "",
            shelfLife: parsedShelfLife,
            expiry: parsedExpiryDate,
            stock: stock ?? "",
            status: finalStatus,
            risks: risks ?? [],
            contraindications: parsedContraindications,
            precautions: parsedPrecautions,
            fallbackFields: fallbackFields ?? [],
            needsConfirmation: parsedNeedsConfirmation,
            note: combinedNote,
            originalText: (originalText ?? "").isEmpty ? originalTextOverride : (originalText ?? ""),
            speechText: speechText ?? "",
            usedSampleFallback: parsedUsedSampleFallback,
            demoOnly: parsedDemoOnly,
            expiryText: expiryText ?? "",
            elderSpeechText: elderSpeechText ?? "",
            dataSource: dataSource ?? "ocr",
            parseQuality: parsedQuality,
            missingFields: parsedMissingFields
            
            
        )
    }

    private static func looksLikeShelfLifeDuration(_ value: String) -> Bool {
        value.range(of: #"[0-9一二三四五六七八九十百]+\s*(天|日|个月|月|年)"#, options: .regularExpression) != nil
            && value.range(of: #"\d{4}[-/.年]\d{1,2}"#, options: .regularExpression) == nil
    }
}

private struct MemberResponse: Decodable {
    var id: Int
    var emoji: String
    var name: String
    var role: String
    var status: String
    var age: String
    var weight: String
    var allergy: String

    func toMember() -> FamilyMember {
        FamilyMember(backendID: id, emoji: emoji, name: name, role: role, status: status, age: age, weight: weight, allergy: allergy)
    }
}

private struct MemberPayload: Encodable {
    var emoji: String
    var name: String
    var role: String
    var status: String
    var age: String
    var weight: String
    var allergy: String

    init(from member: FamilyMember) {
        emoji = member.emoji.isEmpty ? "🙂" : member.emoji
        name = member.name.trimmingCharacters(in: .whitespacesAndNewlines)
        role = member.role
        status = member.status
        age = member.age
        weight = member.weight
        allergy = member.allergy
    }
}

private struct MedicineResponse: Decodable {
    var id: Int
    var emoji: String
    var name: String
    var spec: String
    var category: String
    var owner: String
    var dose: String
    var frequency: String
    var mealTime: String
    var method: String
    var location: String
    var productionDate: String?
    var shelfLife: String?
    // 药品业务接口统一使用 expiry_date；Swift 模型仍使用 expiry 供页面展示。
    var expiryDate: String
    var stock: String
    var status: String
    var risks: [String]
    var note: String
    var originalText: String

    func toMedicine() -> Medicine {
        let rawExpiry = expiryDate.trimmingCharacters(in: .whitespacesAndNewlines)
        let expiryIsDuration = Self.looksLikeShelfLifeDuration(rawExpiry)
        let explicitShelfLife = (shelfLife ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let recoveredShelfLife = Self.extractShelfLife(from: originalText)
        let normalizedShelfLife = explicitShelfLife.isEmpty
            ? (expiryIsDuration ? rawExpiry : recoveredShelfLife)
            : explicitShelfLife

        return Medicine(
            backendID: id,
            emoji: emoji,
            name: name,
            spec: spec,
            category: category,
            owner: owner,
            dose: dose,
            frequency: frequency,
            mealTime: mealTime,
            method: method,
            location: location,
            productionDate: productionDate ?? "",
            shelfLife: normalizedShelfLife,
            expiry: expiryIsDuration ? "" : rawExpiry,
            stock: stock,
            status: status,
            risks: risks,
            note: note,
            originalText: originalText
        )
    }

    private static func looksLikeShelfLifeDuration(_ value: String) -> Bool {
        value.range(of: #"\d+\s*(天|日|个月|月|年)"#, options: .regularExpression) != nil
            && value.range(of: #"\d{4}[-/.年]\d{1,2}"#, options: .regularExpression) == nil
    }

    private static func extractShelfLife(from text: String) -> String {
        guard let regex = try? NSRegularExpression(
            pattern: #"(?:有效期|保质期)\s*[：:]?\s*(\d+\s*(?:个月|月|年|天|日))"#
        ) else { return "" }
        let range = NSRange(text.startIndex..<text.endIndex, in: text)
        guard let match = regex.firstMatch(in: text, range: range),
              let valueRange = Range(match.range(at: 1), in: text) else { return "" }
        return String(text[valueRange]).replacingOccurrences(of: " ", with: "")
    }
}

private struct MedicinePayload: Encodable {
    var emoji: String
    var name: String
    var spec: String
    var category: String
    var owner: String
    var dose: String
    var frequency: String
    var mealTime: String
    var method: String
    var location: String
    var productionDate: String
    var shelfLife: String
    // JSONEncoder 的 convertToSnakeCase 会编码为 expiry_date。
    var expiryDate: String
    var stock: String
    var status: String
    var risks: [String]
    var note: String
    var originalText: String

    init(from medicine: Medicine) {
        emoji = medicine.emoji
        name = medicine.name
        spec = medicine.spec
        category = medicine.category
        owner = medicine.owner
        dose = medicine.dose
        frequency = medicine.frequency
        mealTime = medicine.mealTime
        method = medicine.method
        location = medicine.location
        productionDate = medicine.productionDate
        shelfLife = medicine.shelfLife
        expiryDate = medicine.expiry
        stock = medicine.stock
        status = medicine.status
        risks = medicine.risks
        note = medicine.note
        originalText = medicine.originalText
    }
}

private struct ReminderResponse: Decodable {
    var id: Int
    var medicineId: Int?
    var medicineName: String
    var memberName: String
    var time: String
    var mealLabel: String
    var dose: String
    var status: String
    var isActive: Bool

    func toReminder() -> ReminderPlan {
        ReminderPlan(backendID: id, medicineBackendID: medicineId, medicineName: medicineName, memberName: memberName, time: time, mealLabel: mealLabel, dose: dose, status: status, isActive: isActive)
    }
}

private struct ReminderPayload: Encodable {
    var medicineId: Int?
    var medicineName: String
    var memberName: String
    var time: String
    var mealLabel: String
    var dose: String
    var status: String

    init(from reminder: ReminderPlan) {
        medicineId = reminder.medicineBackendID
        medicineName = reminder.medicineName
        memberName = reminder.memberName
        time = reminder.time
        mealLabel = reminder.mealLabel
        dose = reminder.dose
        status = reminder.status
    }
}

private struct RecordResponse: Decodable {
    var id: Int
    var reminderId: Int?
    var medicineId: Int?
    var memberId: Int?
    var medicineName: String
    var memberName: String
    var dose: String
    var recordedBy: String
    var temperature: String
    var note: String
    var status: String
    var takenAt: String

    func toRecord() -> DoseRecord {
        let metadata = [
            dose.isEmpty ? "已确认" : dose,
            recordedBy.isEmpty ? nil : "\(recordedBy)记录",
            temperature.isEmpty ? nil : "体温 \(temperature)",
            note.isEmpty ? nil : note
        ].compactMap { $0 }.joined(separator: " · ")
        return DoseRecord(
            backendID: id,
            reminderBackendID: reminderId,
            medicineBackendID: medicineId,
            memberBackendID: memberId,
            medicineName: medicineName,
            memberName: memberName,
            dose: dose,
            recordedBy: recordedBy,
            temperature: temperature,
            note: note,
            time: takenAt.displayTimeFromISO,
            title: "\(medicineName) · \(memberName)",
            detail: "\(status) · \(metadata)",
            status: status
        )
    }
}

private struct RecordPayload: Encodable {
    var reminderId: Int?
    var medicineId: Int?
    var memberId: Int?
    var medicineName: String
    var memberName: String
    var dose: String
    var recordedBy: String
    var temperature: String
    var note: String
    var status: String
}

private struct TodayResponse: Decodable {
    var date: String
    var total: Int
    var completed: Int
    var pending: Int
    var items: [TodayItemResponse]

    func toTodayStatus() -> TodayStatus {
        TodayStatus(
            date: date,
            total: total,
            completed: completed,
            pending: pending,
            items: items.enumerated().map { index, item in item.toTodayItem(fallbackID: index) }
        )
    }
}

private struct TodayItemResponse: Decodable {
    var reminderId: Int
    var medicineName: String
    var memberName: String
    var time: String
    var mealLabel: String
    var dose: String
    var status: String
    var recordId: Int?
    var takenAt: String?

    func toTodayItem(fallbackID: Int) -> TodayMedicationItem {
        TodayMedicationItem(
            fallbackID: fallbackID,
            reminderBackendID: reminderId,
            medicineName: medicineName,
            memberName: memberName,
            time: time,
            mealLabel: mealLabel,
            dose: dose,
            status: status,
            recordBackendID: recordId,
            takenAt: takenAt
        )
    }
}

private extension String {
    var displayTimeFromISO: String {
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: self) {
            let output = DateFormatter()
            output.dateFormat = "HH:mm"
            return output.string(from: date)
        }
        if count >= 16 {
            let start = index(startIndex, offsetBy: 11)
            let end = index(start, offsetBy: 5, limitedBy: endIndex) ?? endIndex
            return String(self[start..<end])
        }
        return self
    }
}
