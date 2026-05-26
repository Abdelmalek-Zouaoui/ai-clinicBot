# localization.py
"""
Localization — Simple translation helper for the Clinic Management System.

Usage:
    from localization import t, LANG_CODES
    label = t("msg_invalid_login", lang)

Supported languages: English (en), Arabic (ar), French (fr)
"""

# ── Supported language codes ──────────────────────────────────────────────────
LANG_CODES = ["en", "ar", "fr"]

# ── Translation table ─────────────────────────────────────────────────────────
_TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Authentication ────────────────────────────────────────────────────
    "msg_invalid_login": {
        "en": "Invalid username or password.",
        "ar": "اسم المستخدم أو كلمة المرور غير صحيحة.",
        "fr": "Nom d'utilisateur ou mot de passe incorrect.",
    },
    "msg_login_success": {
        "en": "Login successful!",
        "ar": "تم تسجيل الدخول بنجاح!",
        "fr": "Connexion réussie !",
    },

    # ── General UI ───────────────────────────────────────────────────────
    "btn_save": {
        "en": "Save",
        "ar": "حفظ",
        "fr": "Enregistrer",
    },
    "btn_cancel": {
        "en": "Cancel",
        "ar": "إلغاء",
        "fr": "Annuler",
    },
    "btn_delete": {
        "en": "Delete",
        "ar": "حذف",
        "fr": "Supprimer",
    },
    "btn_edit": {
        "en": "Edit",
        "ar": "تعديل",
        "fr": "Modifier",
    },
    "btn_add": {
        "en": "Add",
        "ar": "إضافة",
        "fr": "Ajouter",
    },
    "btn_search": {
        "en": "Search",
        "ar": "بحث",
        "fr": "Rechercher",
    },
    "btn_clear": {
        "en": "Clear",
        "ar": "مسح",
        "fr": "Effacer",
    },
    "btn_logout": {
        "en": "Logout",
        "ar": "تسجيل الخروج",
        "fr": "Se déconnecter",
    },

    # ── Navigation ────────────────────────────────────────────────────────
    "nav_dashboard": {
        "en": "Dashboard",
        "ar": "لوحة التحكم",
        "fr": "Tableau de bord",
    },
    "nav_patients": {
        "en": "Patients",
        "ar": "المرضى",
        "fr": "Patients",
    },
    "nav_appointments": {
        "en": "Appointments",
        "ar": "المواعيد",
        "fr": "Rendez-vous",
    },
    "nav_prescriptions": {
        "en": "Prescriptions",
        "ar": "الوصفات الطبية",
        "fr": "Ordonnances",
    },
    "nav_services": {
        "en": "Services",
        "ar": "الخدمات",
        "fr": "Services",
    },
    "nav_settings": {
        "en": "Settings",
        "ar": "الإعدادات",
        "fr": "Paramètres",
    },
    "nav_users": {
        "en": "Users",
        "ar": "المستخدمون",
        "fr": "Utilisateurs",
    },

    # ── Patients ─────────────────────────────────────────────────────────
    "msg_patient_saved": {
        "en": "Patient registered successfully!",
        "ar": "تم تسجيل المريض بنجاح!",
        "fr": "Patient enregistré avec succès !",
    },
    "msg_patient_updated": {
        "en": "Patient updated successfully!",
        "ar": "تم تحديث بيانات المريض بنجاح!",
        "fr": "Patient mis à jour avec succès !",
    },
    "msg_patient_deleted": {
        "en": "Patient removed.",
        "ar": "تم حذف المريض.",
        "fr": "Patient supprimé.",
    },
    "err_name_required": {
        "en": "Patient full name is required.",
        "ar": "الاسم الكامل للمريض مطلوب.",
        "fr": "Le nom complet du patient est requis.",
    },
    "err_phone_exists": {
        "en": "A patient with this phone number already exists.",
        "ar": "يوجد مريض بهذا الرقم بالفعل.",
        "fr": "Un patient avec ce numéro existe déjà.",
    },

    # ── Appointments ──────────────────────────────────────────────────────
    "msg_appt_created": {
        "en": "Appointment created!",
        "ar": "تم إنشاء الموعد!",
        "fr": "Rendez-vous créé !",
    },
    "msg_appt_updated": {
        "en": "Appointment updated.",
        "ar": "تم تحديث الموعد.",
        "fr": "Rendez-vous mis à jour.",
    },
    "msg_checkout_done": {
        "en": "Visit completed and receipt generated!",
        "ar": "تمت الزيارة وتم إنشاء الإيصال!",
        "fr": "Visite terminée et reçu généré !",
    },

    # ── Prescriptions ─────────────────────────────────────────────────────
    "msg_rx_saved": {
        "en": "Prescription saved and printed!",
        "ar": "تم حفظ الوصفة وطباعتها!",
        "fr": "Ordonnance enregistrée et imprimée !",
    },
    "err_rx_no_patient": {
        "en": "Select a patient first.",
        "ar": "يرجى اختيار مريض أولاً.",
        "fr": "Veuillez sélectionner un patient d'abord.",
    },
    "err_rx_no_items": {
        "en": "Add at least one medicine.",
        "ar": "أضف دواءً واحداً على الأقل.",
        "fr": "Ajoutez au moins un médicament.",
    },

    # ── Services ──────────────────────────────────────────────────────────
    "msg_service_saved": {
        "en": "Service saved successfully!",
        "ar": "تم حفظ الخدمة بنجاح!",
        "fr": "Service enregistré avec succès !",
    },
    "msg_service_updated": {
        "en": "Service updated successfully!",
        "ar": "تم تحديث الخدمة بنجاح!",
        "fr": "Service mis à jour avec succès !",
    },

    # ── Settings / Backup ─────────────────────────────────────────────────
    "msg_settings_saved": {
        "en": "Settings saved!",
        "ar": "تم حفظ الإعدادات!",
        "fr": "Paramètres enregistrés !",
    },
    "msg_backup_done": {
        "en": "Backup completed successfully.",
        "ar": "تم الاحتياط بنجاح.",
        "fr": "Sauvegarde effectuée avec succès.",
    },
    "msg_backup_failed": {
        "en": "Backup failed.",
        "ar": "فشل الاحتياط.",
        "fr": "Échec de la sauvegarde.",
    },

    # ── Access control ────────────────────────────────────────────────────
    "msg_access_denied": {
        "en": "Admin privileges required.",
        "ar": "يلزم صلاحيات المسؤول.",
        "fr": "Droits administrateur requis.",
    },
}


# ── Public helper ─────────────────────────────────────────────────────────────

def t(key: str, lang: str = "en") -> str:
    """
    Translate a key to the given language.
    Falls back to English if the key or language is not found.
    """
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key                          # return the key itself as fallback
    return entry.get(lang) or entry.get("en") or key