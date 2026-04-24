import random
import pathlib

import pandas as pd
from shiny import App, reactive, render, ui

MBD_BLUE = "#8ebae5"
MBD_RED = "#f19eb1"
MBD_YELLOW = "#fabe50"
RWTH_BLUE = "#00549f"

APP_DIR = pathlib.Path(__file__).parent

CUSTOM_CSS = f"""
    body, .bslib-page-fill {{
        background-color: #f4f8fd;
    }}
    /* White sidebar with pinned footer */
    .sidebar {{
        background-color: #ffffff !important;
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }}
    .sidebar > .sidebar-content {{
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }}
    .sidebar hr {{ margin-top: 0.4rem; margin-bottom: 0.4rem; }}
    /* Select button */
    #select_btn {{
        background-color: {MBD_RED} !important;
        border-color: {MBD_RED} !important;
        color: #1a1a1a !important;
        font-weight: 600;
    }}
    #select_btn:hover {{
        background-color: #e08a9e !important;
        border-color: #e08a9e !important;
    }}
    /* Reset button */
    #reset_btn {{
        border-color: {RWTH_BLUE} !important;
        color: {RWTH_BLUE} !important;
    }}
    #reset_btn:hover {{
        background-color: {RWTH_BLUE} !important;
        color: white !important;
    }}
    /* Download button */
    #download_btn {{
        border-color: {MBD_BLUE} !important;
        color: {MBD_BLUE} !important;
    }}
    #download_btn:hover {{
        background-color: {MBD_BLUE} !important;
        color: white !important;
    }}
    /* Applicants card header */
    .card-header {{
        background-color: {MBD_BLUE};
        color: white;
        font-weight: 600;
    }}
    /* Result card */
    .result-card .card-header {{
        background-color: {MBD_YELLOW} !important;
        color: #1a1a1a !important;
    }}
    .result-card {{
        border-color: {MBD_YELLOW} !important;
    }}
    .result-applicant-card {{
        border-color: {MBD_YELLOW} !important;
    }}
    .result-applicant-card .rank {{
        color: {RWTH_BLUE};
    }}
    /* Sidebar footer — pinned to bottom */
    .sidebar-footer {{
        margin-top: auto;
        padding-top: 1rem;
        border-top: 1px solid #dee2e6;
        text-align: center;
        color: #6c757d;
        font-size: 0.72rem;
    }}
    .sidebar-footer img {{
        max-width: 100%;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    }}
"""

app_ui = ui.page_fillable(
    ui.tags.head(
        ui.tags.style(CUSTOM_CSS),
        ui.tags.script(src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"),
        ui.tags.script("""
            $(document).on('shiny:connected', function() {
                Shiny.addCustomMessageHandler('fire_confetti', function(_) {
                    confetti({
                        particleCount: 180,
                        spread: 90,
                        origin: { y: 0.55 },
                        colors: ['#8ebae5', '#f19eb1', '#fabe50', '#00549f']
                    });
                });
            });
        """),
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.div(
                ui.h4("Weighted Random Selection", class_="d-inline"),
                ui.input_action_button(
                    "reset_btn", "Reset", class_="btn-outline-secondary btn-sm float-end"
                ),
            ),
            ui.hr(),
            ui.output_ui("upload_card"),
            ui.output_ui("config_panel"),
            ui.output_ui("lottery_panel"),
            ui.div(
                ui.tags.img(src="rwth_mbd_bild_rgb.png", style="max-width:100%; border-radius:4px; margin-bottom:0.5rem;"),
                ui.p("Developed by Alan Correa & Julia Kowalski", style="margin:0; font-size:0.72rem;"),
                class_="sidebar-footer",
            ),
            width=340,
            open="always",
        ),
        ui.card(
            ui.card_header("Applicants"),
            ui.output_data_frame("applicants_table"),
            fill=True,
        ),
        ui.output_ui("result_panel"),
        fill=True,
        fillable=True,
    )
)


def server(input, output, session):
    df = reactive.Value(None)
    selected_names = reactive.Value(None)
    reset_counter = reactive.Value(0)

    @render.ui
    def upload_card():
        reset_counter()  # dependency forces re-render on reset, clearing the file input
        return ui.input_file("file", "Upload Excel file (.xlsx / .xls)", accept=[".xlsx", ".xls"])

    @reactive.effect
    @reactive.event(input.reset_btn)
    def do_reset():
        df.set(None)
        selected_names.set(None)
        reset_counter.set(reset_counter() + 1)

    @reactive.effect
    @reactive.event(input.file)
    def load_file():
        file_info = input.file()
        if not file_info:
            return
        path = file_info[0]["datapath"]
        try:
            data = pd.read_excel(path)
            df.set(data)
            selected_names.set(None)
        except Exception as e:
            ui.notification_show(f"Error reading file: {e}", type="error")

    @render.ui
    def config_panel():
        data = df()
        if data is None:
            return ui.div()
        cols = data.columns.tolist()
        return ui.div(
            ui.hr(),
            ui.input_select("name_col", "Applicant name column", choices=cols, selected=cols[0]),
            ui.input_select("score_col", "Score (weight) column", choices=cols, selected=cols[-1]),
            ui.input_select(
                "n_select",
                "Number of applicants to select",
                choices=[str(i) for i in range(1, 11)],
                selected="1",
            ),
        )

    @render.ui
    def lottery_panel():
        if df() is None:
            return ui.div()
        return ui.div(
            ui.input_action_button(
                "select_btn", "Select Applicant(s)", class_="btn-primary w-100 mt-2"
            ),
            ui.output_ui("download_panel"),
        )

    @render.data_frame
    def applicants_table():
        data = df()
        if data is None:
            return pd.DataFrame()
        return data

    @reactive.effect
    @reactive.event(input.select_btn)
    async def run_lottery():
        data = df()
        if data is None:
            return

        score_col = input.score_col()
        name_col = input.name_col()
        n = min(int(input.n_select()), len(data))
        weights = data[score_col].tolist()

        if any(w < 0 for w in weights):
            ui.notification_show("Scores must be non-negative.", type="error")
            return
        if sum(weights) == 0:
            ui.notification_show("At least one score must be greater than zero.", type="error")
            return

        names = data[name_col].tolist()
        chosen = _weighted_sample_without_replacement(names, weights, n)
        selected_names.set(chosen)
        await session.send_custom_message("fire_confetti", {})

    @render.ui
    def result_panel():
        names = selected_names()
        if names is None:
            return ui.div()
        applicant_cards = [
            ui.card(
                ui.card_body(
                    ui.p(f"#{i + 1}", class_="rank mb-1 small fw-bold"),
                    ui.tags.strong(str(name)),
                ),
                class_="result-applicant-card",
            )
            for i, name in enumerate(names)
        ]
        return ui.card(
            ui.card_header(ui.tags.strong("Selected Applicant(s)")),
            ui.div(
                *applicant_cards,
                style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 140px)); gap: 0.75rem; padding: 0.75rem;",
            ),
            class_="result-card shadow",
            fill=False,
        )

    @render.ui
    def download_panel():
        if selected_names() is None:
            return ui.div()
        return ui.download_button(
            "download_btn", "Download Result (.txt)", class_="btn-outline-primary w-100 mt-2"
        )

    @render.download(filename="selected_applicants.txt")
    async def download_btn():
        names = selected_names()
        if names is None:
            return
        yield "\n".join(str(name) for name in names)


def _weighted_sample_without_replacement(population, weights, k):
    indices = list(range(len(population)))
    wts = list(weights)
    selected = []
    for _ in range(k):
        (chosen_pos,) = random.choices(range(len(indices)), weights=wts, k=1)
        selected.append(population[indices[chosen_pos]])
        indices.pop(chosen_pos)
        wts.pop(chosen_pos)
    return selected


app = App(app_ui, server, static_assets=APP_DIR)