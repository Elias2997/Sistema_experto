from __future__ import annotations

import asyncio
import json
import os
import socket
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib import error, request
from urllib.parse import urlparse, urlunparse

import flet as ft

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000/diagnostico")
BACKEND_REQUEST_TIMEOUT_SECONDS = 70
BACKEND_HEALTH_TIMEOUT_SECONDS = 8

APP_BG = "#F4F7F5"
SURFACE = "#FFFFFF"
SURFACE_MUTED = "#F7FBF9"
BORDER = "#D8E7E1"
TEXT = "#10211D"
TEXT_MUTED = "#5B706A"
ACCENT = "#0E7C66"
ACCENT_DARK = "#0A5B4C"
ACCENT_LIGHT = "#DDF5EE"
ACCENT_SOFT = "#EEF9F5"
ERROR_BG = "#FEF0EF"
ERROR_TEXT = "#B42318"
ERROR_BORDER = "#F1C4BF"
SUCCESS_BG = "#E9F8F2"
SUCCESS_TEXT = "#0E7C66"
SUCCESS_BORDER = "#BFE4D2"
WARNING_BG = "#00F7FF"
WARNING_TEXT = "#9A5B13"
WARNING_BORDER = "#FFF9ED"
INFO_BG = "#EAF6F4"
INFO_TEXT = "#0E6B5A"
INFO_BORDER = "#C9E8E0"

SYMPTOMS = [
    "fiebre",
    "tos persistente",
    "dificultad respiratoria",
    "dolor de pecho",
    "dolor abdominal",
    "dolor de cabeza",
    "fatiga",
    "mareos",
    "sed excesiva",
    "vision borrosa",
    "nauseas",
    "vomitos",
]

DISEASE_TYPES = [
    ("general", "General"),
    ("cardiovascular", "Cardiovascular"),
    ("respiratoria", "Respiratoria"),
    ("metabolica", "Metabolica"),
    ("neurologica", "Neurologica"),
    ("digestiva", "Digestiva"),
    ("infecciosa", "Infecciosa"),
]

AGE_OPTIONS = [
    ("pediatrico", "Pediatrico"),
    ("adulto", "Adulto"),
    ("adulto_mayor", "Adulto mayor"),
]

SEX_OPTIONS = [
    ("femenino", "Femenino"),
    ("masculino", "Masculino"),
    ("otro", "Otro"),
]

URGENCY_OPTIONS = [
    ("baja", "Baja"),
    ("media", "Media"),
    ("alta", "Alta"),
]

QUICK_CASES = [
    {
        "label": "Perfil metabolico",
        "tipo": "metabolica",
        "grupo_edad": "adulto",
        "sexo": "otro",
        "urgencia": "media",
        "contexto": "control ambulatorio y evaluacion de sintomas progresivos",
        "sintomas": ["sed excesiva", "vision borrosa", "fatiga"],
    },
    {
        "label": "Perfil respiratorio",
        "tipo": "respiratoria",
        "grupo_edad": "adulto",
        "sexo": "otro",
        "urgencia": "alta",
        "contexto": "triage respiratorio con evolucion aguda",
        "sintomas": ["fiebre", "tos persistente", "dificultad respiratoria"],
    },
    {
        "label": "Dolor toracico",
        "tipo": "cardiovascular",
        "grupo_edad": "adulto",
        "sexo": "masculino",
        "urgencia": "alta",
        "contexto": "dolor de pecho de inicio reciente en sala de observacion",
        "sintomas": ["dolor de pecho", "dificultad respiratoria", "mareos"],
    },
    {
        "label": "Perfil neurologico",
        "tipo": "neurologica",
        "grupo_edad": "adulto",
        "sexo": "femenino",
        "urgencia": "media",
        "contexto": "consulta general por sintomas neurologicos funcionales",
        "sintomas": ["dolor de cabeza", "mareos", "vision borrosa"],
    },
]

CARD_SHADOW = [
    ft.BoxShadow(
        blur_radius=24,
        offset=ft.Offset(0, 10),
        color="#0C4B3D18",
    )
]

TREE_LEVEL_BACKGROUNDS = [
    "#EAF8F4",
    "#F4FBF8",
    "#FAFCFB",
]


@dataclass
class AppState:
    loading: bool = False
    result: dict[str, Any] | None = None
    message: str = "Selecciona sintomas, ajusta el perfil clinico y genera un diagnostico."
    is_error: bool = False
    backend_ready: bool | None = None
    backend_note: str = "Verificando disponibilidad del backend..."
    backend_model: str = "-"


def title_case(value: str) -> str:
    if not value:
        return ""
    return value.replace("_", " ").capitalize()


def format_timestamp(timestamp: str | None) -> str:
    if not timestamp:
        return "Sin timestamp"

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return parsed.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return timestamp


def tone_palette(tone: str) -> tuple[str, str, str]:
    palettes = {
        "accent": (ACCENT_LIGHT, ACCENT_DARK, "#BFE6D9"),
        "success": (SUCCESS_BG, SUCCESS_TEXT, SUCCESS_BORDER),
        "warning": (WARNING_BG, WARNING_TEXT, WARNING_BORDER),
        "error": (ERROR_BG, ERROR_TEXT, ERROR_BORDER),
        "info": (INFO_BG, INFO_TEXT, INFO_BORDER),
        "dark": ("#123E36", "#FFFFFF", "#1D5C51"),
        "neutral": (SURFACE_MUTED, TEXT, BORDER),
        "hero": ("#161313FF", "#070606", "#0F0E0EFF"),
    }
    return palettes.get(tone, palettes["neutral"])


def build_pill(label: str, tone: str = "neutral", icon: ft.Icons | None = None) -> ft.Container:
    bgcolor, color, border_color = tone_palette(tone)
    controls: list[ft.Control] = []

    if icon is not None:
        controls.append(ft.Icon(icon=icon, size=14, color=color))

    controls.append(
        ft.Text(
            label,
            size=12,
            color=color,
            weight=ft.FontWeight.W_600,
        )
    )

    return ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=bgcolor,
        border=ft.border.all(1, border_color),
        border_radius=999,
        content=ft.Row(controls=controls, spacing=6, tight=True),
    )


def build_soft_list(items: list[str], tone: str = "neutral") -> ft.Row:
    if not items:
        return ft.Row(
            wrap=True,
            spacing=8,
            run_spacing=8,
            controls=[
                build_pill(
                    "Sin datos clinicos",
                    tone="neutral",
                    icon=ft.Icons.INFO_OUTLINE_ROUNDED,
                )
            ],
        )

    return ft.Row(
        wrap=True,
        spacing=8,
        run_spacing=8,
        controls=[build_pill(item, tone=tone) for item in items],
    )


def build_placeholder_panel(title: str, message: str, icon: ft.Icons) -> ft.Container:
    return ft.Container(
        padding=28,
        border_radius=24,
        bgcolor=SURFACE_MUTED,
        border=ft.border.all(1, BORDER),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                ft.Container(
                    width=56,
                    height=56,
                    border_radius=18,
                    bgcolor=ACCENT_LIGHT,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icon=icon, color=ACCENT, size=28),
                ),
                ft.Text(
                    title,
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    message,
                    size=13,
                    color=TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )


def build_card(title: str, subtitle: str, icon: ft.Icons, content: ft.Control) -> ft.Container:
    return ft.Container(
        bgcolor=SURFACE,
        border=ft.border.all(1, BORDER),
        border_radius=30,
        padding=24,
        shadow=CARD_SHADOW,
        animate=240,
        content=ft.Column(
            spacing=18,
            controls=[
                ft.Row(
                    spacing=14,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            width=44,
                            height=44,
                            border_radius=16,
                            bgcolor=ACCENT_LIGHT,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Icon(icon=icon, color=ACCENT_DARK, size=22),
                        ),
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(
                                    title,
                                    size=22,
                                    color=TEXT,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Text(subtitle, size=13, color=TEXT_MUTED),
                            ],
                        ),
                    ],
                ),
                content,
            ],
        ),
    )


def build_backend_error_message(payload: dict[str, Any]) -> str:
    error_info = payload.get("error", {}) if isinstance(payload, dict) else {}
    message = error_info.get("message", "El backend devolvio un error.")
    details = error_info.get("details")

    if not details:
        return message

    parts: list[str] = []

    if isinstance(details, dict):
        status = details.get("status")
        provider_code = details.get("providerCode") or details.get("code")
        provider_type = details.get("providerType") or details.get("type")
        provider_message = (
            details.get("providerMessage")
            or details.get("message")
            or details.get("motivo")
        )

        if status:
            parts.append(f"HTTP {status}")
        if provider_code:
            parts.append(str(provider_code))
        if provider_type:
            parts.append(str(provider_type))
        if provider_message:
            parts.append(str(provider_message))
    else:
        parts.append(str(details))

    if not parts:
        return message

    return f"{message} Detalle: {' | '.join(parts)}"


def normalize_backend_url(raw_url: str) -> str:
    normalized = raw_url.strip()

    if not normalized:
        return BACKEND_URL

    if not normalized.startswith(("http://", "https://")):
        normalized = f"http://{normalized}"

    parsed = urlparse(normalized)
    path = parsed.path.rstrip("/")

    if not path or path in {"/", "/health"}:
        path = "/diagnostico"

    return urlunparse(parsed._replace(path=path, params="", query="", fragment=""))


def build_health_url(diagnostico_url: str) -> str:
    parsed = urlparse(diagnostico_url)
    return urlunparse(parsed._replace(path="/health", params="", query="", fragment=""))


def read_error_body(exc: error.HTTPError) -> str:
    raw = exc.read().decode("utf-8")
    try:
        payload = json.loads(raw)
        return build_backend_error_message(payload)
    except json.JSONDecodeError:
        return raw or "El backend devolvio un error no interpretable."


def fetch_backend_health(diagnostico_url: str) -> dict[str, Any]:
    health_url = build_health_url(diagnostico_url)
    with request.urlopen(health_url, timeout=BACKEND_HEALTH_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def diagnose_connection_issue(diagnostico_url: str) -> str:
    health_url = build_health_url(diagnostico_url)

    try:
        payload = fetch_backend_health(diagnostico_url)
        if payload.get("ok"):
            return (
                "El backend responde, pero la URL configurada para el diagnostico no es valida. "
                f"Usa {diagnostico_url}"
            )
    except error.HTTPError as exc:
        return f"El backend respondio con error en /health. Detalle: {read_error_body(exc)}"
    except error.URLError:
        pass

    return (
        "No fue posible conectar con el backend. "
        "Inicia el servidor con `cd backend` y luego `npm run dev`, "
        f"y verifica que responda en {health_url}"
    )


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized_url = normalize_backend_url(url)
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        normalized_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=BACKEND_REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except socket.timeout as exc:
        raise RuntimeError(
            "La consulta al backend tardo demasiado. "
            "El proveedor externo puede estar lento; vuelve a intentar en unos segundos."
        ) from exc
    except error.HTTPError as exc:
        message = read_error_body(exc)
        raise RuntimeError(message) from exc
    except error.URLError as exc:
        raise RuntimeError(diagnose_connection_issue(normalized_url)) from exc


def leaf_node(label: str) -> dict[str, Any]:
    return {"label": label, "children": []}


def build_tree_data(result: dict[str, Any]) -> dict[str, Any]:
    treatment_node = {
        "label": "Tratamiento",
        "children": [leaf_node(item) for item in result.get("tratamiento", [])],
    }
    diagnosis_node = {
        "label": f"Diagnostico: {result.get('diagnostico', '-')}",
        "children": [treatment_node],
    }
    tests_node = {
        "label": "Pruebas sugeridas",
        "children": [
            *[leaf_node(item) for item in result.get("pruebas", [])],
            diagnosis_node,
        ],
    }
    symptoms_node = {
        "label": "Sintomas reportados",
        "children": [
            *[leaf_node(item) for item in result.get("sintomas", [])],
            tests_node,
        ],
    }
    type_node = {
        "label": f"Tipo clinico: {result.get('tipo', '-')}",
        "children": [symptoms_node],
    }
    return {
        "label": f"Enfermedad sugerida: {result.get('enfermedad', '-')}",
        "children": [type_node],
    }


def build_tree_control(node: dict[str, Any], level: int = 0) -> ft.Control:
    children = node.get("children", [])
    label = node.get("label", "")

    if not children:
        return ft.Container(
            margin=ft.margin.only(left=level * 8, bottom=6),
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border_radius=16,
            bgcolor=SURFACE_MUTED,
            border=ft.border.all(1, BORDER),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(icon=ft.Icons.CHECK_CIRCLE_ROUNDED, color=ACCENT, size=16),
                    ft.Text(
                        label,
                        color=TEXT,
                        size=max(12, 14 - min(level, 3)),
                    ),
                ],
            ),
        )

    tree_bg = TREE_LEVEL_BACKGROUNDS[min(level, len(TREE_LEVEL_BACKGROUNDS) - 1)]

    return ft.Container(
        margin=ft.margin.only(left=level * 8, bottom=8),
        border_radius=18,
        border=ft.border.all(1, BORDER),
        bgcolor=tree_bg,
        content=ft.ExpansionTile(
            expanded=level < 2,
            title=ft.Text(
                label,
                color=TEXT,
                size=max(13, 17 - min(level, 3)),
                weight=ft.FontWeight.W_700 if level == 0 else ft.FontWeight.W_600,
            ),
            tile_padding=ft.padding.only(left=14, right=16, top=6, bottom=6),
            controls_padding=ft.padding.only(left=8, right=10, bottom=10),
            icon_color=ACCENT_DARK,
            text_color=TEXT,
            bgcolor=tree_bg,
            controls=[build_tree_control(child, level + 1) for child in children],
        ),
    )


async def main(page: ft.Page) -> None:
    page.title = "Sistema Experto Medico con IA"
    page.padding = 0
    page.bgcolor = APP_BG
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ACCENT)
    page.window_min_width = 390

    state = AppState()
    symptom_chips: dict[str, ft.Chip] = {}

    selected_metric_value = ft.Text(
        "0",
        size=28,
        color="#11100F",
        weight=ft.FontWeight.BOLD,
    )
    backend_metric_value = ft.Text(
        "Verificando",
        size=20,
        color="#11100F",
        weight=ft.FontWeight.BOLD,
    )
    model_metric_value = ft.Text(
        "-",
        size=20,
        color= "#11100F",
        weight=ft.FontWeight.BOLD,
    )

    selected_count_text = ft.Text(
        "0 seleccionados",
        size=12,
        color=ACCENT_DARK,
        weight=ft.FontWeight.W_700,
    )
    selected_preview_row = ft.Row(wrap=True, spacing=8, run_spacing=8)

    backend_status_holder = ft.Container()
    backend_note_text = ft.Text(
        state.backend_note,
        size=13,
        color=TEXT_MUTED,
    )
    backend_model_label = ft.Text(
        "Modelo backend: -",
        size=12,
        color=TEXT_MUTED,
    )

    status_icon = ft.Icon(icon=ft.Icons.MONITOR_HEART_ROUNDED, color=INFO_TEXT, size=18)
    status_text = ft.Text(
        state.message,
        color=INFO_TEXT,
        size=13,
        weight=ft.FontWeight.W_600,
    )
    status_banner = ft.Container(
        bgcolor=INFO_BG,
        border=ft.border.all(1, INFO_BORDER),
        border_radius=18,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
        content=ft.Row(spacing=10, controls=[status_icon, status_text]),
    )

    result_title = ft.Text(
        "Aun no hay una orientacion clinica",
        size=30,
        color=TEXT,
        weight=ft.FontWeight.BOLD,
    )
    result_subtitle = ft.Text(
        "El resumen aparecera despues de generar un caso clinico completo.",
        size=14,
        color=TEXT_MUTED,
    )
    diagnosis_text = ft.Text(
        "La conclusion principal del diagnostico se mostrara aqui.",
        size=15,
        color=ACCENT_DARK,
    )
    explanation_text = ft.Text(
        "La explicacion clinica aparecera aqui cuando el backend responda.",
        size=14,
        color=TEXT_MUTED,
    )
    result_meta_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
    symptom_result_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
    tests_result_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
    treatments_result_row = ft.Row(wrap=True, spacing=8, run_spacing=8)
    tree_host = ft.Container(
        content=build_placeholder_panel(
            "Arbol clinico en espera",
            "Genera un caso para construir la jerarquia enfermedad -> tipo -> sintomas -> pruebas -> diagnostico -> tratamiento.",
            ft.Icons.ACCOUNT_TREE_ROUNDED,
        )
    )

    backend_url_field = ft.TextField(
        label="URL del backend",
        value=BACKEND_URL,
        hint_text="http://localhost:3000/diagnostico",
        prefix_icon=ft.Icons.ROUTER_ROUNDED,
        border_radius=18,
        filled=True,
        fill_color=SURFACE_MUTED,
        border_color=BORDER,
        focused_border_color=ACCENT,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=16),
        text_style=ft.TextStyle(size=13, color=TEXT),
    )
    context_field = ft.TextField(
        label="Contexto clinico",
        hint_text="Ejemplo: control ambulatorio, triage o dolor agudo",
        value="consulta general",
        multiline=True,
        min_lines=2,
        max_lines=4,
        prefix_icon=ft.Icons.DESCRIPTION_OUTLINED,
        border_radius=18,
        filled=True,
        fill_color=SURFACE_MUTED,
        border_color=BORDER,
        focused_border_color=ACCENT,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=16),
    )

    type_selector = ft.SegmentedButton(
        segments=[ft.Segment(value=value, label=label) for value, label in DISEASE_TYPES],
        selected=["general"],
        allow_empty_selection=False,
    )
    age_selector = ft.SegmentedButton(
        segments=[ft.Segment(value=value, label=label) for value, label in AGE_OPTIONS],
        selected=["adulto"],
        allow_empty_selection=False,
    )
    sex_selector = ft.SegmentedButton(
        segments=[ft.Segment(value=value, label=label) for value, label in SEX_OPTIONS],
        selected=["otro"],
        allow_empty_selection=False,
    )
    urgency_selector = ft.SegmentedButton(
        segments=[ft.Segment(value=value, label=label) for value, label in URGENCY_OPTIONS],
        selected=["media"],
        allow_empty_selection=False,
    )

    symptom_chip_grid = ft.Row(wrap=True, spacing=10, run_spacing=10)
    quick_case_row = ft.Row(wrap=True, spacing=10, run_spacing=10)
    loading_ring = ft.ProgressRing(width=18, height=18, stroke_width=2, visible=False, color=ACCENT)

    def build_hero_metric(icon: ft.Icons, label: str, value_control: ft.Text) -> ft.Container:
        return ft.Container(
            padding=18,
            border_radius=22,
            bgcolor="#FFFFFF17",
            border=ft.border.all(1, "#FFFFFF1F"),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(icon=icon, color="#131212", size=18),
                            ft.Text(
                                label,
                                size=12,
                                color="#0D0E0D",
                                weight=ft.FontWeight.W_600,
                            ),
                        ],
                    ),
                    value_control,
                ],
            ),
        )

    hero = ft.Container(
        margin=ft.margin.only(bottom=20),
        border_radius=34,
        gradient=ft.LinearGradient(
            colors=["#0F8B73", "#0C5D53", "#092F35"],
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
        ),
        shadow=CARD_SHADOW,
        content=ft.Stack(
            clip_behavior=ft.ClipBehavior.NONE,
            controls=[
                ft.Container(width=260, height=260, right=-50, top=-80, border_radius=260, bgcolor="#FFFFFF12"),
                ft.Container(width=180, height=180, left=-30, bottom=-60, border_radius=180, bgcolor="#9BE4D01A"),
                ft.Container(
                    padding=32,
                    content=ft.ResponsiveRow(
                        columns=12,
                        controls=[
                            ft.Container(
                                col={"xs": 12, "lg": 7},
                                content=ft.Column(
                                    spacing=18,
                                    controls=[
                                        ft.Row(
                                            wrap=True,
                                            spacing=10,
                                            run_spacing=10,
                                            controls=[
                                                build_pill("Diagnostico clinico asistido", tone="dark", icon=ft.Icons.MEDICAL_SERVICES_ROUNDED),
                                                build_pill("Interfaz renovada", tone="success", icon=ft.Icons.STAR_ROUNDED),
                                            ],
                                        ),
                                        ft.Text(
                                            "Sistema Experto Medico con IA",
                                            size=46,
                                            color="#FFFFFF",
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            "Una consola clinica visual para capturar sintomas, perfilar el caso y leer el resultado en una jerarquia diagnostica clara.",
                                            size=16,
                                            color="#D8F6EF",
                                        ),
                                        ft.Row(
                                            wrap=True,
                                            spacing=10,
                                            run_spacing=10,
                                            
                                            controls=[
                                                build_pill("Casos rapidos", tone= "White", icon=ft.Icons.BOLT_ROUNDED),
                                                build_pill("Respuesta estructurada", tone="White", icon=ft.Icons.DATA_OBJECT_ROUNDED),
                                                build_pill("Arbol interactivo", tone="White", icon=ft.Icons.ACCOUNT_TREE_ROUNDED),
                                            ],
                                        ),
                                    ],
                                ),
                            ),
                            ft.Container(
                                col={"xs": 12, "lg": 5},
                                content=ft.Column(
                                    spacing=12,
                                    controls=[
                                        build_hero_metric(ft.Icons.MONITOR_HEART_ROUNDED, "Estado backend", backend_metric_value),
                                        build_hero_metric(ft.Icons.INFO_OUTLINE_ROUNDED, "Sintomas activos", selected_metric_value),
                                        build_hero_metric(ft.Icons.AUTO_AWESOME_ROUNDED, "Modelo reportado", model_metric_value),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    def selected_symptoms() -> list[str]:
        return [name for name, chip in symptom_chips.items() if chip.selected]

    def first_selected_value(control: ft.SegmentedButton, fallback: str) -> str:
        return control.selected[0] if control.selected else fallback

    def set_feedback(message: str, tone: str = "info") -> None:
        state.message = message
        state.is_error = tone == "error"

        tone_map = {
            "success": (ft.Icons.CHECK_CIRCLE_ROUNDED, SUCCESS_BG, SUCCESS_TEXT, SUCCESS_BORDER),
            "warning": (ft.Icons.WARNING_AMBER_ROUNDED, WARNING_BG, WARNING_TEXT, WARNING_BORDER),
            "error": (ft.Icons.ERROR_OUTLINE_ROUNDED, ERROR_BG, ERROR_TEXT, ERROR_BORDER),
            "info": (ft.Icons.MONITOR_HEART_ROUNDED, INFO_BG, INFO_TEXT, INFO_BORDER),
        }
        icon, bgcolor, color, border_color = tone_map.get(tone, tone_map["info"])

        status_icon.icon = icon
        status_icon.color = color
        status_text.value = message
        status_text.color = color
        status_banner.bgcolor = bgcolor
        status_banner.border = ft.border.all(1, border_color)

    def refresh_selected_preview() -> None:
        current = selected_symptoms()
        selected_metric_value.value = str(len(current))
        selected_count_text.value = (
            f"{len(current)} seleccionados" if current else "Sin sintomas seleccionados"
        )
        selected_preview_row.controls = (
            [build_pill(title_case(item), tone="accent") for item in current]
            if current
            else [build_pill("Activa sintomas para perfilar el caso", tone="neutral", icon=ft.Icons.LIGHTBULB_OUTLINE_ROUNDED)]
        )

    def set_backend_status(ok: bool | None, note: str, model: str = "-") -> None:
        state.backend_ready = ok
        state.backend_note = note
        state.backend_model = model or "-"

        if ok is True:
            backend_status_holder.content = build_pill("Backend conectado", tone="success", icon=ft.Icons.CLOUD_DONE_ROUNDED)
            backend_metric_value.value = "Conectado"
        elif ok is False:
            backend_status_holder.content = build_pill("Backend sin conexion", tone="error", icon=ft.Icons.CLOUD_OFF_ROUNDED)
            backend_metric_value.value = "Sin conexion"
        else:
            backend_status_holder.content = build_pill("Verificando backend", tone="info", icon=ft.Icons.SYNC_ROUNDED)
            backend_metric_value.value = "Verificando"

        backend_note_text.value = note
        backend_model_label.value = f"Modelo backend: {state.backend_model}"
        model_metric_value.value = state.backend_model

    def render_result(result: dict[str, Any]) -> None:
        meta = result.get("meta", {})
        model = meta.get("modelo", "-")
        attempts = meta.get("intentos", "-")
        timestamp = format_timestamp(meta.get("timestamp"))
        tone = "warning" if model == "reglas-locales" else "accent"

        result_title.value = result.get("enfermedad", "-")
        result_subtitle.value = (
            f"Clasificacion clinica: {result.get('tipo', '-')} | Intentos: {attempts}"
        )
        diagnosis_text.value = result.get("diagnostico", "-")
        explanation_text.value = result.get("explicacion", "-")
        result_meta_row.controls = [
            build_pill(f"Modelo: {model}", tone=tone, icon=ft.Icons.AUTO_AWESOME_ROUNDED),
            build_pill(f"Actualizado: {timestamp}", tone="neutral", icon=ft.Icons.SCHEDULE_ROUNDED),
            build_pill(
                f"Sintomas: {len(result.get('sintomas', []))}",
                tone="info",
                icon=ft.Icons.MONITOR_HEART_ROUNDED,
            ),
        ]
        symptom_result_row.controls = build_soft_list(result.get("sintomas", []), tone="info").controls
        tests_result_row.controls = build_soft_list(result.get("pruebas", []), tone="accent").controls
        treatments_result_row.controls = build_soft_list(result.get("tratamiento", []), tone="success").controls
        tree_host.content = build_tree_control(build_tree_data(result))

    def reset_result_view() -> None:
        result_title.value = "Aun no hay una orientacion clinica"
        result_subtitle.value = "El resumen aparecera despues de generar un caso clinico completo."
        diagnosis_text.value = "La conclusion principal del diagnostico se mostrara aqui."
        explanation_text.value = "La explicacion clinica aparecera aqui cuando el backend responda."
        result_meta_row.controls = [
            build_pill(
                "Esperando respuesta del backend",
                tone="neutral",
                icon=ft.Icons.HOURGLASS_TOP_ROUNDED,
            )
        ]
        symptom_result_row.controls = build_soft_list([], tone="neutral").controls
        tests_result_row.controls = build_soft_list([], tone="neutral").controls
        treatments_result_row.controls = build_soft_list([], tone="neutral").controls
        tree_host.content = build_placeholder_panel(
            "Arbol clinico en espera",
            "Todavia no se ha generado un resultado para construir la jerarquia clinica.",
            ft.Icons.ACCOUNT_TREE_ROUNDED,
        )

    async def refresh_backend_status(_: ft.ControlEvent | None = None, show_feedback: bool = False) -> None:
        normalized_url = normalize_backend_url(backend_url_field.value)
        backend_url_field.value = normalized_url
        set_backend_status(None, "Verificando disponibilidad del backend...", state.backend_model)
        page.update()

        try:
            health = await asyncio.to_thread(fetch_backend_health, normalized_url)
            model = health.get("modelo", "-")
            note = f"Backend operativo en {build_health_url(normalized_url)}"
            set_backend_status(True, note, model)
            if show_feedback:
                set_feedback("Backend verificado correctamente.", tone="success")
        except Exception as exc:
            set_backend_status(False, str(exc), "-")
            if show_feedback:
                set_feedback(f"No se pudo verificar el backend: {exc}", tone="error")

        page.update()

    def select_case(case: dict[str, Any]) -> None:
        for name, chip in symptom_chips.items():
            chip.selected = name in case["sintomas"]

        type_selector.selected = [case["tipo"]]
        age_selector.selected = [case["grupo_edad"]]
        sex_selector.selected = [case["sexo"]]
        urgency_selector.selected = [case["urgencia"]]
        context_field.value = case["contexto"]
        refresh_selected_preview()
        set_feedback(f"Se aplico el caso rapido: {case['label']}.", tone="info")
        page.update()

    def clear_form(_: ft.ControlEvent | None = None) -> None:
        for chip in symptom_chips.values():
            chip.selected = False

        type_selector.selected = ["general"]
        age_selector.selected = ["adulto"]
        sex_selector.selected = ["otro"]
        urgency_selector.selected = ["media"]
        context_field.value = "consulta general"
        backend_url_field.value = normalize_backend_url(BACKEND_URL)
        state.result = None
        refresh_selected_preview()
        reset_result_view()
        set_feedback("Formulario restablecido. Listo para un nuevo caso.", tone="info")
        page.update()

    def on_symptom_select(_: ft.ControlEvent) -> None:
        refresh_selected_preview()
        page.update()

    for symptom in SYMPTOMS:
        chip = ft.Chip(
            data=symptom,
            label=title_case(symptom),
            selected=False,
            show_checkmark=False,
            bgcolor=SURFACE_MUTED,
            selected_color=ACCENT_LIGHT,
            elevation=0,
            elevation_on_click=0,
            color="#FFFFFF",
            on_select=on_symptom_select,
        )
        symptom_chips[symptom] = chip
        symptom_chip_grid.controls.append(chip)

    for quick_case in QUICK_CASES:
        quick_case_row.controls.append(
            ft.Chip(
                label=quick_case["label"],
                leading=ft.Icon(icon=ft.Icons.BOLT_ROUNDED, color=ACCENT_DARK, size=16),
                bgcolor=ACCENT_SOFT,
                color= "#FFFFFF",
                on_click=lambda _event, case=quick_case: select_case(case),
            )
        )

    analyze_button = ft.ElevatedButton(
        "Generar diagnostico",
        icon=ft.Icons.AUTO_AWESOME_ROUNDED,
        height=52,
        style=ft.ButtonStyle(
            bgcolor=ACCENT,
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=18),
            padding=ft.padding.symmetric(horizontal=20, vertical=18),
        ),
    )
    verify_button = ft.ElevatedButton(
        "Verificar backend",
        icon=ft.Icons.MONITOR_HEART_OUTLINED,
        height=52,
        style=ft.ButtonStyle(
            bgcolor="#E8F6F2",
            color=ACCENT_DARK,
            shape=ft.RoundedRectangleBorder(radius=18),
            padding=ft.padding.symmetric(horizontal=18, vertical=18),
        ),
        on_click=lambda event: page.run_task(refresh_backend_status, event, True),
    )
    clear_button = ft.ElevatedButton(
        "Limpiar",
        icon=ft.Icons.RESTART_ALT_ROUNDED,
        height=52,
        style=ft.ButtonStyle(
            bgcolor=SURFACE_MUTED,
            color=TEXT,
            shape=ft.RoundedRectangleBorder(radius=18),
            padding=ft.padding.symmetric(horizontal=18, vertical=18),
        ),
        on_click=clear_form,
    )

    symptoms_card = build_card(
        "Mapa de sintomas",
        "Selecciona los hallazgos clinicos mas relevantes y usa casos rapidos para simular escenarios frecuentes.",
        ft.Icons.HEALTH_AND_SAFETY_ROUNDED,
        ft.Column(
            spacing=18,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Casos rapidos", size=15, color=TEXT, weight=ft.FontWeight.W_700),
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            bgcolor=ACCENT_LIGHT,
                            border_radius=999,
                            content=selected_count_text,
                        ),
                    ],
                ),
                quick_case_row,
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Vista previa de sintomas activos", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_600),
                        selected_preview_row,
                    ],
                ),
                ft.Divider(height=1, color=BORDER),
                ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Sintomas disponibles", size=15, color=TEXT, weight=ft.FontWeight.W_700),
                        symptom_chip_grid,
                    ],
                ),
            ],
        ),
    )

    profile_card = build_card(
        "Perfil clinico",
        "Ajusta el contexto del caso, controla la conexion y lanza el analisis cuando el perfil este listo.",
        ft.Icons.MONITOR_HEART_ROUNDED,
        ft.Column(
            spacing=18,
            controls=[
                ft.Column(spacing=8, controls=[ft.Text("Tipo de enfermedad", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_600), type_selector]),
                ft.Column(spacing=8, controls=[ft.Text("Grupo de edad", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_600), age_selector]),
                ft.Column(spacing=8, controls=[ft.Text("Sexo", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_600), sex_selector]),
                ft.Column(spacing=8, controls=[ft.Text("Nivel de urgencia", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_600), urgency_selector]),
                context_field,
                backend_url_field,
                ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[analyze_button, verify_button, clear_button, loading_ring]),
                ft.Container(
                    padding=18,
                    border_radius=22,
                    bgcolor=SURFACE_MUTED,
                    border=ft.border.all(1, BORDER),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Row(
                                spacing=10,
                                wrap=True,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    backend_status_holder,
                                    build_pill("Ruta de salud: /health", tone="neutral", icon=ft.Icons.LINK_ROUNDED),
                                ],
                            ),
                            backend_note_text,
                            backend_model_label,
                        ],
                    ),
                ),
            ],
        ),
    )

    result_card = build_card(
        "Resultado clinico",
        "Lectura priorizada del diagnostico, su clasificacion y la metadata de ejecucion devuelta por el backend.",
        ft.Icons.AUTO_AWESOME_MOTION_ROUNDED,
        ft.Column(
            spacing=18,
            controls=[
                ft.Column(spacing=6, controls=[result_title, result_subtitle]),
                ft.Container(
                    padding=20,
                    border_radius=22,
                    bgcolor=ACCENT_LIGHT,
                    border=ft.border.all(1, "#C7EBDD"),
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("Diagnostico orientativo", size=12, color=ACCENT_DARK, weight=ft.FontWeight.W_700),
                            diagnosis_text,
                        ],
                    ),
                ),
                result_meta_row,
                ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Sintomas incorporados al resultado", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_700),
                        symptom_result_row,
                    ],
                ),
            ],
        ),
    )

    plan_card = build_card(
        "Pruebas y tratamiento",
        "Resume los estudios sugeridos y la ruta terapeutica propuesta en una vista facil de explorar.",
        ft.Icons.FACT_CHECK_ROUNDED,
        ft.Column(
            spacing=18,
            controls=[
                ft.Column(spacing=8, controls=[ft.Text("Pruebas sugeridas", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_700), tests_result_row]),
                ft.Column(spacing=8, controls=[ft.Text("Tratamiento o siguientes pasos", size=13, color=TEXT_MUTED, weight=ft.FontWeight.W_700), treatments_result_row]),
            ],
        ),
    )

    explanation_card = build_card(
        "Explicacion del diagnostico",
        "Descripcion narrativa para entender por que el backend llego a esa orientacion clinica.",
        ft.Icons.SPEAKER_NOTES_ROUNDED,
        ft.Container(
            padding=20,
            border_radius=24,
            bgcolor=SURFACE_MUTED,
            border=ft.border.all(1, BORDER),
            content=explanation_text,
        ),
    )

    tree_card = build_card(
        "Arbol jerarquico dinamico",
        "Visualiza la progresion enfermedad -> tipo -> sintomas -> pruebas -> diagnostico -> tratamiento en un panel interactivo.",
        ft.Icons.ACCOUNT_TREE_ROUNDED,
        ft.Container(
            height=520,
            content=ft.Column(scroll=ft.ScrollMode.AUTO, controls=[tree_host]),
        ),
    )

    layout = ft.Container(
        padding=26,
        content=ft.Column(
            spacing=18,
            controls=[
                hero,
                status_banner,
                ft.ResponsiveRow(
                    columns=12,
                    run_spacing=18,
                    controls=[
                        ft.Container(col={"xs": 12, "lg": 5}, content=ft.Column(spacing=18, controls=[symptoms_card, profile_card])),
                        ft.Container(col={"xs": 12, "lg": 7}, content=ft.Column(spacing=18, controls=[result_card, plan_card, explanation_card, tree_card])),
                    ],
                ),
            ],
        ),
    )

    async def submit_diagnosis(_: ft.ControlEvent) -> None:
        current_symptoms = selected_symptoms()

        if not current_symptoms:
            set_feedback("Selecciona al menos un sintoma antes de consultar.", tone="warning")
            page.update()
            return

        payload = {
            "sintomas": current_symptoms,
            "tipoEnfermedad": first_selected_value(type_selector, "general"),
            "grupoEdad": first_selected_value(age_selector, "adulto"),
            "sexo": first_selected_value(sex_selector, "otro"),
            "nivelUrgencia": first_selected_value(urgency_selector, "media"),
            "contextoClinico": context_field.value,
        }

        state.loading = True
        loading_ring.visible = True
        analyze_button.disabled = True
        verify_button.disabled = True
        clear_button.disabled = True
        backend_url_field.value = normalize_backend_url(backend_url_field.value)
        set_feedback("Consultando backend y estructurando el caso clinico...", tone="info")
        page.update()

        try:
            result = await asyncio.to_thread(post_json, backend_url_field.value.strip(), payload)

            if not isinstance(result, dict) or not result.get("ok"):
                raise RuntimeError("La respuesta del backend no contiene un resultado valido.")

            state.result = result
            render_result(result)
            set_feedback("Diagnostico generado correctamente.", tone="success")
        except Exception as exc:
            state.result = None
            reset_result_view()
            diagnosis_text.value = "No se pudo generar el diagnostico."
            explanation_text.value = str(exc)
            tree_host.content = build_placeholder_panel(
                "No fue posible construir el arbol",
                str(exc),
                ft.Icons.ERROR_OUTLINE_ROUNDED,
            )
            set_feedback(str(exc), tone="error")
        finally:
            loading_ring.visible = False
            analyze_button.disabled = False
            verify_button.disabled = False
            clear_button.disabled = False
            state.loading = False
            page.update()

    analyze_button.on_click = submit_diagnosis

    refresh_selected_preview()
    reset_result_view()
    set_backend_status(None, "Verificando disponibilidad del backend...", "-")

    page.add(ft.SafeArea(content=layout))
    page.run_task(refresh_backend_status)
