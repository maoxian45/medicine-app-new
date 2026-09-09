import Foundation
import UserNotifications

final class NotificationService {
    static let shared = NotificationService()

    static func dailyReminderTitle(medicineName: String, memberName: String) -> String {
        "服药提醒 · \(memberName) · \(medicineName)"
    }

    private init() {}

    func requestPermission() async -> Bool {
        do {
            return try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])
        } catch {
            return false
        }
    }

    func scheduleDemoReminder(title: String, body: String, secondsFromNow: TimeInterval = 8) async throws {
        _ = await requestPermission()

        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: max(5, secondsFromNow), repeats: false)
        let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: trigger)

        try await UNUserNotificationCenter.current().add(request)
    }

    func scheduleDailyReminder(title: String, body: String, hour: Int, minute: Int) async throws {
        _ = await requestPermission()

        var dateComponents = DateComponents()
        dateComponents.hour = hour
        dateComponents.minute = minute

        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default

        let trigger = UNCalendarNotificationTrigger(dateMatching: dateComponents, repeats: true)
        let request = UNNotificationRequest(identifier: Self.dailyReminderIdentifier(title: title, hour: hour, minute: minute), content: content, trigger: trigger)
        try await UNUserNotificationCenter.current().add(request)
    }

    func cancelDailyReminder(medicineName: String, memberName: String, time: String) {
        let parts = time.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return }
        let title = Self.dailyReminderTitle(medicineName: medicineName, memberName: memberName)
        let identifier = Self.dailyReminderIdentifier(title: title, hour: parts[0], minute: parts[1])
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [identifier])
    }

    private static func dailyReminderIdentifier(title: String, hour: Int, minute: Int) -> String {
        "\(title)-\(hour)-\(minute)"
    }
}
