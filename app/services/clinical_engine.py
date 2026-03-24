from typing import Dict, Any
from app.models.clinical_models import ClinicalCase
from app.services.reasoning_engine import ReasoningEngine
from app.services.protocol_engine import ProtocolEngine
from app.services.llm_extractor import LLMExtractor
from app.services.safety_engine import assess_case_safety


class ClinicalEngine:

    def __init__(self):
        self.reasoning = ReasoningEngine()
        self.protocol = ProtocolEngine()
        self.llm_extractor = LLMExtractor()

    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:

        # =========================
        # 1. MIGRA CONTEXTO
        # =========================
        case = ClinicalCase.from_legacy_context(context)

        case.history.append({
            "role": "user",
            "content": message
        })

        # =========================
        # 2. EXTRAÇÃO COM LLM
        # =========================
        self._llm_extraction(case, message, context)

        # =========================
        # 3. GARANTE SCENARIO (fallback)
        # =========================
        if not case.clinical_context.scenario:
            case.clinical_context.scenario = self._detect_scenario(message)

        # =========================
        # 4. CONTEXTO LEGADO
        # =========================
        legacy_context = case.to_legacy_context()

        # =========================
        # 5. REASONING
        # =========================
        reasoning_output = self.reasoning.analyze(legacy_context)

        case.reasoning.status = reasoning_output.get("status")
        case.reasoning.missing_data = reasoning_output.get("missing_data", [])
        case.reasoning.confidence = reasoning_output.get("confidence")
        case.reasoning.risk_level = reasoning_output.get("risk_level")

        # =========================
        # 6. PROTOCOLO
        # =========================
        if case.reasoning.status == "ready_for_treatment":
            protocol_output = self.protocol.apply_protocol(legacy_context)

            case.treatment_plan.diagnostico_provavel = protocol_output.get("diagnostico")
            case.treatment_plan.conduta = protocol_output.get("conduta")
            case.treatment_plan.medicacao = protocol_output.get("medicacao")
            case.treatment_plan.dose = protocol_output.get("dose")
            case.treatment_plan.posologia = protocol_output.get("posologia")
            case.treatment_plan.duracao = protocol_output.get("duracao")
            case.treatment_plan.justificativa = protocol_output.get("justificativa")

        # =========================
        # 7. SEGURANÇA (CORRIGIDO)
        # =========================
        safety_output = assess_case_safety(
            scenario=legacy_context.get("scenario"),
            dados_clinicos=legacy_context.get("dados_clinicos"),
            confidence=case.reasoning.confidence
        )

        case.safety.nivel_seguranca = safety_output.get("nivel_seguranca")
        case.safety.reavaliacao_necessaria = safety_output.get("reavaliacao_necessaria", False)
        case.safety.alertas_clinicos = safety_output.get("alertas_clinicos", [])
        case.safety.dados_relevantes_ausentes = safety_output.get("dados_relevantes_ausentes", [])

        # =========================
        # 8. DOCUMENTOS (PREPARAÇÃO)
        # =========================
        if case.treatment_plan.medicacao:
            case.documents.recipe_ready = True
            case.documents.document_type = "receita_simples"

        # =========================
        # 9. RESPOSTA FINAL
        # =========================
        response_text = self._build_response(case)

        return {
            "resposta": response_text,
            "clinical_response": {
                "tipo": self._define_tipo(case),
                "confidence": case.reasoning.confidence,
                "risk_level": case.reasoning.risk_level,
                "nivel_seguranca": case.safety.nivel_seguranca,
                "reavaliacao_necessaria": case.safety.reavaliacao_necessaria,
                "alertas_clinicos": case.safety.alertas_clinicos,
                "dados_relevantes_ausentes": case.safety.dados_relevantes_ausentes
            }
        }

    # =========================
    # 🔥 EXTRAÇÃO COM LLM
    # =========================
    def _llm_extraction(self, case: ClinicalCase, message: str, context: Dict[str, Any]):

        extracted = self.llm_extractor.extract(message, context)

        if not extracted:
            return

        # PACIENTE
        case.patient.idade = extracted.get("idade") or case.patient.idade
        case.patient.peso = extracted.get("peso") or case.patient.peso
        case.patient.sexo = extracted.get("sexo") or case.patient.sexo

        # SCENARIO
        case.clinical_context.scenario = extracted.get("scenario") or case.clinical_context.scenario

        # SINTOMAS
        symptoms = extracted.get("symptoms", {})
        for key, value in symptoms.items():
            if hasattr(case.clinical_context.symptoms, key) and value is not None:
                setattr(case.clinical_context.symptoms, key, value)

        # RISCO
        risks = extracted.get("risk_factors", {})
        for key, value in risks.items():
            if hasattr(case.clinical_context.risk_factors, key) and value is not None:
                setattr(case.clinical_context.risk_factors, key, value)

    # =========================
    # AUXILIARES
    # =========================

    def _detect_scenario(self, message: str) -> str:
        msg = message.lower()

        if "ouvido" in msg:
            return "otite_media_aguda"
        if "garganta" in msg:
            return "faringite"
        if "sinus" in msg:
            return "sinusite"

        return "geral"

    def _build_response(self, case: ClinicalCase) -> str:

        parts = []

        if case.treatment_plan.diagnostico_provavel:
            parts.append(f"Diagnóstico provável: {case.treatment_plan.diagnostico_provavel}")

        if case.treatment_plan.conduta:
            parts.append(f"Conduta recomendada: {case.treatment_plan.conduta}")

        if case.treatment_plan.medicacao:
            parts.append(f"Medicação: {case.treatment_plan.medicacao}")

        if case.treatment_plan.dose:
            parts.append(f"Dose: {case.treatment_plan.dose}")

        if case.treatment_plan.posologia:
            parts.append(f"Posologia: {case.treatment_plan.posologia}")

        if case.treatment_plan.duracao:
            parts.append(f"Duração: {case.treatment_plan.duracao}")

        if case.treatment_plan.justificativa:
            parts.append(f"Justificativa: {case.treatment_plan.justificativa}")

        if case.safety.alertas_clinicos:
            parts.append("\nAlertas clínicos:")
            for alerta in case.safety.alertas_clinicos:
                parts.append(f"• {alerta}")

        if case.reasoning.missing_data:
            parts.append("\nDados necessários:")
            for item in case.reasoning.missing_data:
                parts.append(f"• {item}")

        return "\n".join(parts)

    def _define_tipo(self, case: ClinicalCase) -> str:
        if case.reasoning.status != "ready_for_treatment":
            return "coleta_dados"
        return "protocolo_definido"
