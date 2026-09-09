import Foundation

enum MockData {
    static let ibuprofen = Medicine(
        emoji: "💊",
        name: "布洛芬缓释胶囊",
        spec: "0.3g × 20 粒",
        category: "常备药",
        owner: "我",
        dose: "1 粒",
        frequency: "2 次",
        mealTime: "饭后",
        method: "温水送服",
        location: "客厅药箱",
        expiry: "2026-12",
        stock: "16 粒",
        status: "正常",
        risks: ["慎用", "过敏", "胃溃疡", "饭后", "不得同时使用"],
        note: "不要与其他含布洛芬成分的药物重复服用。若出现过敏反应、胃部不适或其他异常情况，请停止使用并咨询医生或药师。",
        originalText: "示例 OCR 文本：用法用量 一次 1 粒，一日 2 次，饭后服用。胃溃疡、孕妇慎用。"
    )

    static let medicines: [Medicine] = [
        ibuprofen,
        Medicine(
            emoji: "🧴",
            name: "布洛芬混悬液",
            spec: "100ml · 混悬液",
            category: "退热药",
            owner: "小宝",
            dose: "5ml",
            frequency: "需核对",
            mealTime: "遵医嘱",
            method: "摇匀后服用",
            location: "家庭药箱",
            expiry: "2026-06",
            stock: "半瓶",
            status: "需核对",
            risks: ["剂量核对", "间隔", "遵医嘱"],
            note: "剂量请核对正式说明书，并遵循医生或药师建议。多人照护时先看上次记录时间。",
            originalText: ""
        ),
        Medicine(
            emoji: "💊",
            name: "感冒灵颗粒",
            spec: "10g × 9 袋",
            category: "常备药",
            owner: "我",
            dose: "1 袋",
            frequency: "需要时",
            mealTime: "饭后",
            method: "温水冲服",
            location: "卧室抽屉",
            expiry: "12 天后",
            stock: "3 袋",
            status: "快过期",
            risks: ["嗜睡", "有效期"],
            note: "即将过期，建议检查是否继续保留。",
            originalText: ""
        ),
        Medicine(
            emoji: "❤️",
            name: "降压药",
            spec: "5mg × 30 片",
            category: "长期用药",
            owner: "爷爷",
            dose: "1 片",
            frequency: "2 次",
            mealTime: "饭后",
            method: "温水送服",
            location: "床头柜",
            expiry: "2027-03",
            stock: "少于 5 天",
            status: "库存少",
            risks: ["长期用药", "不能漏服"],
            note: "每天按时服药，不要自行停药或加量。如果头晕、心跳加快，请马上告诉家人或联系医生。",
            originalText: ""
        ),
        Medicine(
            emoji: "💊",
            name: "胃药",
            spec: "20mg × 14 粒",
            category: "长期用药",
            owner: "爷爷",
            dose: "1 粒",
            frequency: "1 次",
            mealTime: "午饭后",
            method: "饭后服用",
            location: "客厅药箱",
            expiry: "2027-06",
            stock: "20 天量",
            status: "正常",
            risks: ["饭后"],
            note: "按说明书或医生建议服用。",
            originalText: ""
        )
    ]

    static let members: [FamilyMember] = [
        FamilyMember(emoji: "👩", name: "我", role: "家庭管理员", status: "今日 1 项用药 · 已完成", age: "", weight: "-", allergy: "无"),
        FamilyMember(emoji: "👴", name: "爷爷", role: "老人慢病用药", status: "今日 3 次提醒 · 已完成 2 次", age: "76 岁", weight: "68kg", allergy: "无"),
        FamilyMember(emoji: "👵", name: "奶奶", role: "长期用药", status: "长期用药 2 种 · 药品状态正常", age: "73 岁", weight: "60kg", allergy: "无"),
        FamilyMember(emoji: "👶", name: "小宝", role: "家庭成员", status: "退热药上次记录 14:10 · 妈妈记录", age: "4 岁", weight: "17kg", allergy: "青霉素")
    ]

    static let reminders: [ReminderPlan] = [
        ReminderPlan(medicineName: "降压药", memberName: "爷爷", time: "08:00", mealLabel: "早餐后", dose: "1 片", status: "已确认"),
        ReminderPlan(medicineName: "胃药", memberName: "爷爷", time: "12:30", mealLabel: "午餐后", dose: "1 粒", status: "已确认"),
        ReminderPlan(medicineName: "降压药", memberName: "爷爷", time: "20:00", mealLabel: "晚餐后", dose: "1 片", status: "待确认")
    ]

    static let records: [DoseRecord] = [
        DoseRecord(time: "08:05", title: "布洛芬缓释胶囊 · 我", detail: "已服药 · 1 粒 · 饭后", status: "已服药"),
        DoseRecord(time: "08:06", title: "降压药 · 爷爷", detail: "已服药 · 老人端确认", status: "已服药"),
        DoseRecord(time: "14:10", title: "布洛芬混悬液 · 小宝", detail: "已服药 · 妈妈记录 · 同步给家属", status: "已服药"),
        DoseRecord(time: "20:00", title: "降压药 · 爷爷", detail: "待确认 · 可电话提醒", status: "待确认"),
        DoseRecord(time: "20:10", title: "胃药 · 奶奶", detail: "稍后提醒 · 10 分钟后再次通知", status: "稍后")
    ]
}
