"""LLM helpers for clinic workflows.

This module is meant to be imported by the desktop app, not run as a
standalone interactive chat loop.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import json
from groq import APIConnectionError, APIStatusError, Groq, RateLimitError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()


class ClinicLLMService:
    """High-level AI assistant for clinic operations."""

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "search_patients",
                "description": "Rechercher des patients par nom, telephone, ou e-mail pour obtenir leur patient_id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Le nom, le numero de telephone ou l'e-mail a rechercher"
                        }
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_patient_record",
                "description": "Retrieve a full patient record by patient_id",
                "parameters": {
                    "type": "object",
                    "properties": {"patient_id": {"type": "integer"}},
                    "required": ["patient_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_today_appointments",
                "description": "Return today's appointments",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_appointment",
                "description": "Creer un nouveau rendez-vous",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "patient_id": {"type": "integer"},
                        "doctor_id": {"type": "integer"},
                        "date": {"type": "string"},
                        "visit_type": {"type": "string"},
                        "chief_complaint": {"type": "string"},
                    },
                    "required": ["patient_id", "doctor_id", "date", "visit_type", "chief_complaint"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_diagnosis",
                "description": "Mettre a jour le diagnostic et les notes d'un rendez-vous existant",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "appointment_id": {"type": "integer"},
                        "diagnosis": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                    "required": ["appointment_id", "diagnosis", "notes"],
                },
            },
        },
    ]

    def __init__(self, db_manager: Any | None = None, model: str | None = None):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key) if api_key else None
        self.db = db_manager
        self.model = model or self.DEFAULT_MODEL
        self.history = [
            {
                "role": "system",
                "content": (
                    "Tu es un assistant médical intelligent intégré dans le logiciel de gestion d'une clinique. "
                    "Tu as un accès DIRECT à la base de données de la clinique via des outils (tools). "
                    "Tu PEUX et DOIS utiliser ces outils dès que l'utilisateur demande des informations sur des patients, "
                    "des rendez-vous, ou toute autre donnée de la clinique. "
                    "Ne dis JAMAIS que tu n'as pas accès à la base de données — tu l'as via tes outils. "
                    "\n\n"
                    "Outils disponibles :\n"
                    "• search_patients(query) — recherche des patients par nom, téléphone ou e-mail pour obtenir leur ID\n"
                    "• get_patient_record(patient_id) — récupère le dossier complet d'un patient (infos, rendez-vous, prescriptions)\n"
                    "• get_today_appointments() — liste tous les rendez-vous du jour\n"
                    "• create_appointment(...) — crée un nouveau rendez-vous\n"
                    "• update_diagnosis(appointment_id, diagnosis, notes) — met à jour le diagnostic d'un rendez-vous\n"
                    "\n"
                    "Règles STRICTES :\n"
                    "• Réponds toujours en français, de façon concise et professionnelle.\n"
                    "• Si l'utilisateur mentionne un nom de patient sans ID, commence par chercher son ID avec search_patients.\n"
                    "• Si l'utilisateur demande de résumer ou de chercher un patient mais ne fournit aucun nom, e-mail, téléphone ni ID, ne lance pas d'outil. Demande-lui de préciser le nom ou le téléphone du patient.\n"
                    "• Ne jamais appeler d'outil avec des valeurs génériques, fictives ou manquantes (comme 'nom du patient', 'query' ou des ID imaginaires). Si tu n'as pas de valeur réelle à rechercher, pose la question à l'utilisateur.\n"
                    "• NE JAMAIS imbriquer les appels de fonctions. Tu ne peux pas appeler get_patient_record avec le résultat de search_patients dans la même étape. Appelle d'abord search_patients, attends que l'outil te retourne l'ID du patient, puis à l'étape suivante, appelle get_patient_record avec cet ID.\n"
                    "• NE JAMAIS générer à la fois du texte de discussion et un appel d'outil (tool call) dans le même message. Si tu décides d'appeler un outil, laisse le contenu de ton message vide (pas de texte) et génère uniquement le tool call.\n"
                    "• Rappelle toujours que tes suggestions ne remplacent pas le jugement du médecin.\n"
                    "• Si une action n'est pas possible avec tes outils, explique clairement ce que tu peux faire à la place."
                ),
            }
        ]

    def chat(self, message_utilisateur: str, reset_history: bool = False) -> str:
        if not self.client:
            return "GROQ_API_KEY manquant."

        if reset_history:
            self.reset_history()

        self.history.append({"role": "user", "content": message_utilisateur})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                max_tokens=1024,
                temperature=0.2,
                tool_choice="none",
            )

            msg = response.choices[0].message
            final_message = msg.content or ""
            self.history.append({"role": "assistant", "content": final_message})
            return final_message

        except RateLimitError:
            self.history.pop()
            return "Limite de requetes atteinte."

        except APIConnectionError:
            self.history.pop()
            return "Erreur de connexion reseau."

        except APIStatusError as error:
            self.history.pop()
            return f"Erreur API ({error.status_code})."

    def reset_history(self) -> None:
        self.history = [self.history[0]]

    def run_agent(self, objectif: str, max_steps: int = 10) -> str:
        if not self.client:
            return "GROQ_API_KEY manquant."

        self.history.append({"role": "user", "content": objectif})

        try:
            step = 0
            while step < max_steps:
                step += 1
                print(f"[agent] Étape {step}/{max_steps}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.history,
                    max_tokens=1024,
                    temperature=0.2,
                    tools=self.TOOLS,
                    tool_choice="auto",
                )

                choice = response.choices[0]
                msg = choice.message
                finish_reason = getattr(choice, "finish_reason", None)
                self.history.append(msg)

                if finish_reason != "tool_calls":
                    final_message = msg.content or ""
                    print(f"[agent] Réponse finale obtenue à l'étape {step}")
                    return final_message

                tool_calls = getattr(msg, "tool_calls", []) or []
                for tc in tool_calls:
                    name = tc.function.name
                    args = tc.function.arguments
                    parsed_args = args
                    if isinstance(parsed_args, str):
                        try:
                            parsed_args = json.loads(parsed_args)
                        except Exception:
                            parsed_args = {}
                    result_json = self._execute_tool(name, parsed_args)
                    print(f"[agent] Outil exécuté : {name}")
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": name,
                        "content": result_json,
                    })

            print(f"[agent] Arrêt forcé après {max_steps} étapes")
            return f"Arrêt forcé : nombre maximum d'étapes atteint ({max_steps})."

        except RateLimitError:
            last_user = max(i for i, m in enumerate(self.history) if m.get("role") == "user")
            self.history = self.history[:last_user]
            return "Limite de requetes atteinte."

        except APIConnectionError:
            last_user = max(i for i, m in enumerate(self.history) if m.get("role") == "user")
            self.history = self.history[:last_user]
            return "Erreur de connexion reseau."

        except APIStatusError as error:
            last_user = max(i for i, m in enumerate(self.history) if m.get("role") == "user")
            self.history = self.history[:last_user]
            return f"Erreur API ({error.status_code})."

    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        if tool_name == "search_patients":
            result = self.search_patients(tool_args["query"])
            return json.dumps(result, ensure_ascii=False)
        if tool_name == "get_patient_record":
            result = self.get_patient_record(tool_args["patient_id"])
            return json.dumps(result or {"erreur": "introuvable"}, ensure_ascii=False)
        if tool_name == "get_today_appointments":
            result = self.get_today_appointments()
            return json.dumps(result, ensure_ascii=False)
        if tool_name == "create_appointment":
            sql = (
                "INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, visit_type, chief_complaint) "
                "VALUES (?, ?, ?, 'Pending', ?, ?)"
            )
            params = (
                tool_args["patient_id"],
                tool_args["doctor_id"],
                tool_args["date"],
                tool_args["visit_type"],
                tool_args["chief_complaint"],
            )
            result = self.db.execute_query(sql, params) if self.db else False
            return json.dumps({"succes": bool(result)}, ensure_ascii=False)
        if tool_name == "update_diagnosis":
            sql = "UPDATE appointments SET diagnosis = ?, notes = ? WHERE appointment_id = ?"
            params = (
                tool_args["diagnosis"],
                tool_args["notes"],
                tool_args["appointment_id"],
            )
            result = self.db.execute_query(sql, params) if self.db else False
            return json.dumps({"succes": bool(result)}, ensure_ascii=False)
        return json.dumps({"erreur": f"outil inconnu : {tool_name}"})

    def get_today_appointments(self) -> list[dict]:
        if not self.db:
            return []

        rows = self.db.fetch_all(
            """SELECT a.appointment_id, a.patient_id, p.full_name,
                      a.doctor_id, a.appointment_date, a.status,
                      a.visit_type, a.chief_complaint,
                      a.diagnosis, a.notes, a.total_amount
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               WHERE DATE(a.appointment_date) = DATE('now')
                 AND a.status NOT IN ('Cancelled','No Show')
               ORDER BY a.appointment_date""",
            (),
        )
        return [self._appointment_row(row) for row in (rows or [])]

    def search_patients(self, query: str) -> list[dict]:
        if not self.db:
            return []
        like = f"%{query}%"
        rows = self.db.fetch_all(
            """SELECT patient_id, full_name, date_of_birth, phone
               FROM patients
               WHERE full_name LIKE ? OR phone LIKE ? OR email LIKE ?""",
            (like, like, like),
        )
        return [
            {
                "patient_id": r[0],
                "full_name": r[1] or "",
                "date_of_birth": r[2] or "",
                "phone": r[3] or "",
            }
            for r in (rows or [])
        ]

    def get_patient_record(self, patient_id: int) -> dict[str, Any] | None:
        if not self.db:
            return None

        patient = self.db.fetch_one(
            """SELECT patient_id, full_name, date_of_birth, gender,
                      phone, email, address, wilaya, blood_type,
                      allergies, medical_history, notes, created_at
               FROM patients WHERE patient_id=?""",
            (patient_id,),
        )
        if not patient:
            return None

        appointments = self.db.fetch_all(
            """SELECT a.appointment_id, a.appointment_date, a.status,
                      a.visit_type, a.chief_complaint, a.diagnosis, a.notes
               FROM appointments a
               WHERE a.patient_id=?
               ORDER BY a.appointment_date DESC""",
            (patient_id,),
        )

        prescriptions = self.db.fetch_all(
            """SELECT rx.rx_id, rx.issued_date, rx.notes
               FROM prescriptions rx
               WHERE rx.patient_id=?
               ORDER BY rx.issued_date DESC""",
            (patient_id,),
        )

        return {
            "patient": self._patient_row(patient),
            "appointments": [self._appointment_history_row(row) for row in (appointments or [])],
            "prescriptions": [
                {
                    "rx_id": row[0],
                    "issued_date": row[1] or "",
                    "notes": row[2] or "",
                }
                for row in (prescriptions or [])
            ],
        }

    def summarize_patient_record(self, patient_id: int) -> str:
        record = self.get_patient_record(patient_id)
        if not record:
            return "Patient introuvable."

        prompt = (
            "Fais un resume medical court et utile pour le medecin a partir des donnees suivantes. "
            "Mets en avant les antecedents, allergies, problemes recents, motifs de consultation et prescriptions. "
            "Si des donnees manquent, dis-le simplement.\n\n"
            f"Dossier patient:\n{record}"
        )
        return self.run_agent(prompt, max_steps=10)

    def suggest_diagnoses(
        self,
        chief_complaint: str,
        patient_context: dict[str, Any] | None = None,
    ) -> str:
        context_text = patient_context or {}
        prompt = (
            "A partir du symptome principal, propose 3 a 5 hypotheses diagnostiques possibles. "
            "Ajoute les examens ou signes d'alerte importants, puis les classes de traitements souvent utilisees. "
            "Ne donne pas de posologie definitive. Signale que la decision finale revient au medecin.\n\n"
            f"Symptome principal: {chief_complaint}\n"
            f"Contexte patient: {context_text}"
        )
        return self.run_agent(prompt, max_steps=10)

    @staticmethod
    def _appointment_row(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "appointment_id": row[0],
            "patient_id": row[1],
            "patient_name": row[2] or "",
            "doctor_id": row[3],
            "appointment_date": row[4] or "",
            "status": row[5] or "Pending",
            "visit_type": row[6] or "",
            "chief_complaint": row[7] or "",
            "diagnosis": row[8] or "",
            "notes": row[9] or "",
            "total_amount": float(row[10] or 0),
        }

    @staticmethod
    def _appointment_history_row(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "appointment_id": row[0],
            "appointment_date": row[1] or "",
            "status": row[2] or "",
            "visit_type": row[3] or "",
            "chief_complaint": row[4] or "",
            "diagnosis": row[5] or "",
            "notes": row[6] or "",
        }

    @staticmethod
    def _patient_row(row: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "patient_id": row[0],
            "full_name": row[1] or "",
            "date_of_birth": row[2] or "",
            "gender": row[3] or "Other",
            "phone": row[4] or "",
            "email": row[5] or "",
            "address": row[6] or "",
            "wilaya": row[7] or "",
            "blood_type": row[8] or "",
            "allergies": row[9] or "",
            "medical_history": row[10] or "",
            "notes": row[11] or "",
            "created_at": row[12] or "",
        }


if __name__ == "__main__":
    service = ClinicLLMService()
    print(service.chat("Bonjour, explique-moi ton role dans la clinique.", reset_history=True))