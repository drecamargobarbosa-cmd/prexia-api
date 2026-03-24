from typing import List, Optional, Literal
from pydantic import BaseModel, Field


ConfidenceLevel = Literal["baixa", "moderada", "alta"]
RiskLevel = Literal["baixo", "moderado", "alto"]
SafetyLevel = Literal["adequado", "atencao", "critico", "incerto"]
ReasoningStatus = Literal[
    "insufficient_data",
    "need_more_data",
    "ready_for_treatment"
]


class PatientData(BaseModel):
    user_id: str = "default"
    idade: Optional[int] = None
    peso: Optional[float] = None
    sexo: Optional[str] = None


class SymptomsData(BaseModel):
    dor_presente: Optional[bool] = None
    dor_intensa: Optional[bool] = None
    febre: Optional[bool] = None
    febre_alta: Optional[bool] = None
    toxemia: Optional[bool] = None
    prostracao: Optional[bool] = None
    duracao_dias: Optional[int] = None

    secrecao_auricular: Optional[bool] = None
    secrecao_purulenta: Optional[bool] = None

    dor_garganta: Optional[bool] = None
    placas_amigdalianas: Optional[bool] = None

    dor_facial: Optional[bool] = None
    secrecao_nasal_purulenta: Optional[bool] = None


class RiskFactorsData(BaseModel):
    alergia_penicilina: Optional[bool] = None
    gestante: Optional[bool] = None
    lactante: Optional[bool] = None
    doenca_renal: Optional[bool] = None
    hepatopatia: Optional[bool] = None


class ClinicalContextData(BaseModel):
    scenario: Optional[str] = None
    intent: str = "geral"
    symptoms: SymptomsData = Field(default_factory=SymptomsData)
    risk_factors: RiskFactorsData = Field(default_factory=RiskFactorsData)


class ReasoningData(BaseModel):
    status: ReasoningStatus = "insufficient_data"
    missing_data: List[str] = Field(default_factory=list)
    confidence: Optional[ConfidenceLevel] = None
    risk_level: Optional[RiskLevel] = None


class TreatmentPlanData(BaseModel):
    diagnostico_provavel: Optional[str] = None
    conduta: Optional[str] = None
    medicacao: Optional[str] = None
    dose: Optional[str] = None
    posologia: Optional[str] = None
    duracao: Optional[str] = None
    justificativa: Optional[str] = None
    observacoes: List[str] = Field(default_factory=list)


class SafetyData(BaseModel):
    nivel_seguranca: SafetyLevel = "incerto"
    reavaliacao_necessaria: bool = False
    alertas_clinicos: List[str] = Field(default_factory=list)
    dados_relevantes_ausentes: List[str] = Field(default_factory=list)


class DocumentsData(BaseModel):
    recipe_ready: bool = False
    document_type: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ClinicalCase(BaseModel):
    patient: PatientData = Field(default_factory=PatientData)
    clinical_context: ClinicalContextData = Field(default_factory=ClinicalContextData)
    reasoning: ReasoningData = Field(default_factory=ReasoningData)
    treatment_plan: TreatmentPlanData = Field(default_factory=TreatmentPlanData)
    safety: SafetyData = Field(default_factory=SafetyData)
    documents: DocumentsData = Field(default_factory=DocumentsData)
    history: List[HistoryItem] = Field(default_factory=list)

    def to_legacy_context(self) -> dict:
        """
        Mantém compatibilidade com a estrutura atual do projeto.
        Isso permite migração gradual sem quebrar o motor existente.
        """
        return {
            "scenario": self.clinical_context.scenario,
            "intent": self.clinical_context.intent,
            "history": [item.model_dump() for item in self.history],
            "dados_clinicos": {
                "idade": self.patient.idade,
                "peso": self.patient.peso,
                "alergia": self.clinical_context.risk_factors.alergia_penicilina,
                "gravidade": None,
                "febre": self.clinical_context.symptoms.febre,
                "febre_alta": self.clinical_context.symptoms.febre_alta,
                "dor_presente": self.clinical_context.symptoms.dor_presente,
                "dor_intensa": self.clinical_context.symptoms.dor_intensa,
                "toxemia": self.clinical_context.symptoms.toxemia,
                "prostracao": self.clinical_context.symptoms.prostracao,
                "secrecao_auricular": self.clinical_context.symptoms.secrecao_auricular,
                "secrecao_purulenta": self.clinical_context.symptoms.secrecao_purulenta,
                "duracao_dias": self.clinical_context.symptoms.duracao_dias,
                "dor_garganta": self.clinical_context.symptoms.dor_garganta,
                "placas_amigdalianas": self.clinical_context.symptoms.placas_amigdalianas,
                "dor_facial": self.clinical_context.symptoms.dor_facial,
                "secrecao_nasal_purulenta": self.clinical_context.symptoms.secrecao_nasal_purulenta,
            }
        }

    @classmethod
    def from_legacy_context(cls, context: Optional[dict], user_id: str = "default") -> "ClinicalCase":
        """
        Converte a estrutura antiga para o novo schema.
        Essa função é a ponte da migração.
        """
        context = context or {}
        dados = context.get("dados_clinicos", {}) or {}
        history = context.get("history", []) or []

        history_items: List[HistoryItem] = []
        for item in history:
            role = item.get("role")
            content = item.get("content")
            if role in ["user", "assistant"] and isinstance(content, str):
                history_items.append(HistoryItem(role=role, content=content))

        return cls(
            patient=PatientData(
                user_id=user_id,
                idade=dados.get("idade"),
                peso=dados.get("peso"),
                sexo=None,
            ),
            clinical_context=ClinicalContextData(
                scenario=context.get("scenario"),
                intent=context.get("intent", "geral"),
                symptoms=SymptomsData(
                    dor_presente=dados.get("dor_presente"),
                    dor_intensa=dados.get("dor_intensa"),
                    febre=dados.get("febre"),
                    febre_alta=dados.get("febre_alta"),
                    toxemia=dados.get("toxemia"),
                    prostracao=dados.get("prostracao"),
                    duracao_dias=dados.get("duracao_dias"),
                    secrecao_auricular=dados.get("secrecao_auricular"),
                    secrecao_purulenta=dados.get("secrecao_purulenta"),
                    dor_garganta=dados.get("dor_garganta"),
                    placas_amigdalianas=dados.get("placas_amigdalianas"),
                    dor_facial=dados.get("dor_facial"),
                    secrecao_nasal_purulenta=dados.get("secrecao_nasal_purulenta"),
                ),
                risk_factors=RiskFactorsData(
                    alergia_penicilina=dados.get("alergia"),
                    gestante=None,
                    lactante=None,
                    doenca_renal=None,
                    hepatopatia=None,
                ),
            ),
            history=history_items,
        )
