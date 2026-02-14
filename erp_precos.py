from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from tkinter import messagebox, ttk

import customtkinter as ctk

from erp.application.quote_service import QuoteService
from erp.domain.models import PurchaseInput, QuoteRecord, SaleInput, parse_decimal
from erp.domain.pricing_engine import PricingEngine
from erp.infrastructure.database import Database
from erp.infrastructure.quote_repository import QuoteRepository


class PricingERPApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ERP Comercial de Gestao de Precos")
        self.geometry("1380x860")
        self.minsize(1180, 760)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.service = self._build_service()

        self.current_quote_id: int | None = None
        self.current_quote_version = 1
        self.last_result = None
        self.last_driver = "margin"

        self._suspend_auto_updates = False
        self._updating_from_price = False
        self._updating_from_margin = False

        self._build_ui()
        self._bind_events()
        self._load_defaults()
        self._sync_markup_state()
        self.recalculate_all()
        self.refresh_history()
        self._set_quote_info()

    def _build_service(self) -> QuoteService:
        database_path = Path("data") / "erp_comercial.db"
        database = Database(str(database_path))
        database.initialize()
        repository = QuoteRepository(database)
        return QuoteService(pricing_engine=PricingEngine(), repository=repository)

    def _build_ui(self):
        shell = ctk.CTkFrame(self, corner_radius=0, fg_color="#eef2f7")
        shell.pack(fill="both", expand=True)

        self._build_header(shell)
        self._build_meta_bar(shell)

        main = ctk.CTkFrame(shell, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_purchase_panel(main)
        self._build_sales_panel(main)
        self._build_history_panel(main)

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="#0f172a", corner_radius=0, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="ERP Comercial | Formacao de Precos",
            text_color="#f8fafc",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left", padx=22, pady=18)

        ctk.CTkLabel(
            header,
            text="Atalhos: Ctrl+S salvar | Ctrl+N nova | F5 atualizar",
            text_color="#cbd5e1",
            font=ctk.CTkFont(size=12),
        ).pack(side="right", padx=20, pady=24)

    def _build_meta_bar(self, parent):
        meta = ctk.CTkFrame(parent, fg_color="#ffffff", corner_radius=14)
        meta.pack(fill="x", padx=16, pady=12)
        for col in range(5):
            meta.grid_columnconfigure(col, weight=1 if col < 4 else 0)

        self.product_var = ctk.StringVar(value="")
        self.category_var = ctk.StringVar(value="")
        self.supplier_var = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="RASCUNHO")

        self._meta_field(meta, 0, "Produto", self.product_var, 230)
        self._meta_field(meta, 1, "Categoria", self.category_var, 180)
        self._meta_field(meta, 2, "Fornecedor", self.supplier_var, 230)

        ctk.CTkLabel(meta, text="Status", text_color="#334155").grid(
            row=0, column=3, sticky="w", padx=8, pady=(10, 4)
        )
        self.status_menu = ctk.CTkOptionMenu(
            meta,
            values=["RASCUNHO", "APROVADA", "ARQUIVADA"],
            variable=self.status_var,
            width=140,
        )
        self.status_menu.grid(row=1, column=3, sticky="w", padx=8, pady=(0, 8))

        actions = ctk.CTkFrame(meta, fg_color="transparent")
        actions.grid(row=0, column=4, rowspan=2, sticky="e", padx=8, pady=8)
        ctk.CTkButton(actions, text="Nova Cotacao", command=self.new_quote, width=130).pack(
            side="left", padx=4
        )
        ctk.CTkButton(actions, text="Salvar Cotacao", command=self.save_quote, width=130).pack(
            side="left", padx=4
        )

        self.quote_info_label = ctk.CTkLabel(
            meta,
            text="Cotacao: Nova",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#0f172a",
        )
        self.quote_info_label.grid(row=2, column=0, columnspan=5, sticky="w", padx=8, pady=(2, 2))

    def _meta_field(self, parent, col: int, label_text: str, variable: ctk.StringVar, width: int):
        ctk.CTkLabel(parent, text=label_text, text_color="#334155").grid(
            row=0, column=col, sticky="w", padx=8, pady=(10, 4)
        )
        ctk.CTkEntry(parent, textvariable=variable, width=width).grid(
            row=1, column=col, sticky="w", padx=8, pady=(0, 8)
        )

    def _card_title(self, parent, text):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#0f172a",
        ).pack(anchor="w", padx=16, pady=(12, 8))

    def _field(self, parent, row, label_text, var, kind="text"):
        ctk.CTkLabel(parent, text=label_text, text_color="#334155", anchor="w").grid(
            row=row, column=0, sticky="w", padx=10, pady=6
        )
        entry = ctk.CTkEntry(parent, textvariable=var, width=130)
        entry.grid(row=row, column=1, sticky="e", padx=10, pady=6)

        if kind == "money":
            entry.bind("<FocusOut>", lambda _e, v=var: self._format_money_var(v))
            entry.bind("<Return>", lambda _e, v=var: self._format_money_var(v))
        elif kind == "pct":
            entry.bind("<FocusOut>", lambda _e, v=var: self._format_percent_var(v))
            entry.bind("<Return>", lambda _e, v=var: self._format_percent_var(v))
        return entry

    def _tax_row_credit(self, parent, row, name, rate_var, credit_var):
        ctk.CTkLabel(parent, text=f"{name} (%)", text_color="#334155", anchor="w").grid(
            row=row, column=0, sticky="w", padx=10, pady=6
        )
        entry = ctk.CTkEntry(parent, textvariable=rate_var, width=90)
        entry.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=6)
        entry.bind("<FocusOut>", lambda _e, v=rate_var: self._format_percent_var(v))
        entry.bind("<Return>", lambda _e, v=rate_var: self._format_percent_var(v))

        ctk.CTkCheckBox(
            parent,
            text="Credita",
            variable=credit_var,
            onvalue=1,
            offvalue=0,
            text_color="#334155",
            width=95,
        ).grid(row=row, column=2, sticky="e", padx=10, pady=6)

    def _tax_row_no_credit(self, parent, row, name, rate_var, note):
        ctk.CTkLabel(parent, text=f"{name} (%)", text_color="#334155", anchor="w").grid(
            row=row, column=0, sticky="w", padx=10, pady=6
        )
        entry = ctk.CTkEntry(parent, textvariable=rate_var, width=90)
        entry.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=6)
        entry.bind("<FocusOut>", lambda _e, v=rate_var: self._format_percent_var(v))
        entry.bind("<Return>", lambda _e, v=rate_var: self._format_percent_var(v))

        ctk.CTkLabel(parent, text=note, text_color="#64748b").grid(
            row=row, column=2, sticky="e", padx=10, pady=6
        )

    def _build_purchase_panel(self, main):
        panel = ctk.CTkFrame(main, fg_color="#ffffff", corner_radius=16)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self._card_title(panel, "Compra / Cotacao")

        content = ctk.CTkFrame(panel, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=8)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)

        self.compra_liquida_var = ctk.StringVar(value="100.00")
        self.ipi_var = ctk.StringVar(value="5.00")
        self.st_var = ctk.StringVar(value="8.00")
        self.icms_compra_var = ctk.StringVar(value="18.00")
        self.pis_compra_var = ctk.StringVar(value="1.65")
        self.cofins_compra_var = ctk.StringVar(value="7.60")

        self.credita_icms_var = ctk.IntVar(value=1)
        self.credita_pis_var = ctk.IntVar(value=1)
        self.credita_cofins_var = ctk.IntVar(value=1)

        ctk.CTkLabel(content, text="Preco de Compra Liquido (R$)", text_color="#334155").grid(
            row=0, column=0, sticky="w", padx=10, pady=(6, 10)
        )
        compra_entry = ctk.CTkEntry(content, textvariable=self.compra_liquida_var, width=180)
        compra_entry.grid(row=0, column=1, columnspan=2, sticky="w", padx=10, pady=(6, 10))
        compra_entry.bind("<FocusOut>", lambda _e: self._format_money_var(self.compra_liquida_var))
        compra_entry.bind("<Return>", lambda _e: self._format_money_var(self.compra_liquida_var))

        self._tax_row_no_credit(content, 1, "IPI", self.ipi_var, "Sem credito")
        self._tax_row_no_credit(content, 2, "ST", self.st_var, "Sem credito")
        self._tax_row_credit(content, 3, "ICMS", self.icms_compra_var, self.credita_icms_var)
        self._tax_row_credit(content, 4, "PIS", self.pis_compra_var, self.credita_pis_var)
        self._tax_row_credit(content, 5, "COFINS", self.cofins_compra_var, self.credita_cofins_var)

        ctk.CTkFrame(content, height=2, fg_color="#e2e8f0").grid(
            row=6, column=0, columnspan=3, sticky="ew", padx=6, pady=10
        )

        self.valor_impostos_compra_label = ctk.CTkLabel(content, text="Impostos Totais na Compra: R$ 0,00")
        self.valor_impostos_compra_label.grid(row=7, column=0, columnspan=3, sticky="w", padx=10, pady=3)

        self.creditos_compra_label = ctk.CTkLabel(content, text="Creditos Tributarios na Compra: R$ 0,00")
        self.creditos_compra_label.grid(row=8, column=0, columnspan=3, sticky="w", padx=10, pady=3)

        self.custo_efetivo_label = ctk.CTkLabel(
            content,
            text="Custo Efetivo (base para venda): R$ 0,00",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#16a34a",
        )
        self.custo_efetivo_label.grid(row=9, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 3))

    def _build_sales_panel(self, main):
        panel = ctk.CTkFrame(main, fg_color="#ffffff", corner_radius=16)
        panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        self._card_title(panel, "Venda / Formacao de Preco")

        content = ctk.CTkFrame(panel, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=8)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        kpi = ctk.CTkFrame(content, fg_color="#f8fafc", corner_radius=10)
        kpi.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(2, 10))
        for c in range(3):
            kpi.grid_columnconfigure(c, weight=1)

        self.kpi_preco = ctk.CTkLabel(kpi, text="Preco Final\nR$ 0,00", font=ctk.CTkFont(size=14, weight="bold"))
        self.kpi_preco.grid(row=0, column=0, sticky="ew", padx=6, pady=8)
        self.kpi_lucro = ctk.CTkLabel(kpi, text="Lucro Liquido\nR$ 0,00", font=ctk.CTkFont(size=14, weight="bold"))
        self.kpi_lucro.grid(row=0, column=1, sticky="ew", padx=6, pady=8)
        self.kpi_margem = ctk.CTkLabel(kpi, text="Margem Liquida\n0,00%", font=ctk.CTkFont(size=14, weight="bold"))
        self.kpi_margem.grid(row=0, column=2, sticky="ew", padx=6, pady=8)

        self.pis_venda_var = ctk.StringVar(value="1.65")
        self.cofins_venda_var = ctk.StringVar(value="7.60")
        self.icms_venda_var = ctk.StringVar(value="18.00")
        self.aplica_acrescimo_var = ctk.IntVar(value=0)
        self.acrescimo_percentual_var = ctk.StringVar(value="0.00")
        self.margem_cld_var = ctk.StringVar(value="25.00")
        self.preco_venda_var = ctk.StringVar(value="0.00")

        self._field(content, 1, "PIS Venda (%)", self.pis_venda_var, kind="pct")
        self._field(content, 2, "COFINS Venda (%)", self.cofins_venda_var, kind="pct")
        self._field(content, 3, "ICMS Venda (%)", self.icms_venda_var, kind="pct")

        acrescimo_frame = ctk.CTkFrame(content, fg_color="transparent")
        acrescimo_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(2, 8))
        acrescimo_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkCheckBox(
            acrescimo_frame,
            text="Aplicar acrescimo no preco de venda",
            variable=self.aplica_acrescimo_var,
            onvalue=1,
            offvalue=0,
        ).grid(row=0, column=0, sticky="w")

        self.acrescimo_entry = ctk.CTkEntry(acrescimo_frame, textvariable=self.acrescimo_percentual_var, width=90)
        self.acrescimo_entry.grid(row=0, column=1, sticky="e")
        self.acrescimo_entry.bind("<FocusOut>", lambda _e: self._format_percent_var(self.acrescimo_percentual_var))
        self.acrescimo_entry.bind("<Return>", lambda _e: self._format_percent_var(self.acrescimo_percentual_var))
        ctk.CTkLabel(acrescimo_frame, text="%", text_color="#334155").grid(
            row=0, column=2, sticky="w", padx=(6, 0)
        )

        ctk.CTkFrame(content, height=2, fg_color="#e2e8f0").grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=6, pady=10
        )

        self._field(content, 6, "Margem de Lucro CLD (%)", self.margem_cld_var, kind="pct")
        self._field(content, 7, "Preco de Venda (R$)", self.preco_venda_var, kind="money")

        buttons = ctk.CTkFrame(content, fg_color="transparent")
        buttons.grid(row=8, column=0, columnspan=2, sticky="ew", padx=10, pady=8)
        buttons.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            buttons,
            text="Calcular Preco pela Margem",
            command=lambda: self.calculate_price_from_margin(show_errors=True),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            buttons,
            text="Calcular Margem pelo Preco",
            command=lambda: self.calculate_margin_from_price(show_errors=True),
            fg_color="#0891b2",
            hover_color="#0e7490",
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ctk.CTkFrame(content, height=2, fg_color="#e2e8f0").grid(
            row=9, column=0, columnspan=2, sticky="ew", padx=6, pady=10
        )

        self.impostos_venda_label = ctk.CTkLabel(content, text="Impostos de Venda (R$): R$ 0,00")
        self.impostos_venda_label.grid(row=10, column=0, columnspan=2, sticky="w", padx=10, pady=2)

        self.lucro_liquido_label = ctk.CTkLabel(content, text="Lucro Liquido na Venda: R$ 0,00")
        self.lucro_liquido_label.grid(row=11, column=0, columnspan=2, sticky="w", padx=10, pady=2)

        self.margem_cld_result_label = ctk.CTkLabel(content, text="Margem CLD Calculada: 0,00%")
        self.margem_cld_result_label.grid(row=12, column=0, columnspan=2, sticky="w", padx=10, pady=2)

        self.margem_liquida_venda_label = ctk.CTkLabel(content, text="Margem Liquida na Venda: 0,00%")
        self.margem_liquida_venda_label.grid(row=13, column=0, columnspan=2, sticky="w", padx=10, pady=2)

        self.acrescimo_valor_label = ctk.CTkLabel(content, text="Acrescimo sobre venda: R$ 0,00")
        self.acrescimo_valor_label.grid(row=14, column=0, columnspan=2, sticky="w", padx=10, pady=2)

        self.margem_real_label = ctk.CTkLabel(
            content,
            text="Margem Real: 0,00%",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#16a34a",
        )
        self.margem_real_label.grid(row=15, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 2))

        self.calc_status_label = ctk.CTkLabel(content, text="Calculo automatico ativo", text_color="#64748b")
        self.calc_status_label.grid(row=16, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 2))

    def _build_history_panel(self, main):
        panel = ctk.CTkFrame(main, fg_color="#ffffff", corner_radius=16)
        panel.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text="Historico de Cotacoes",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        table_wrap = ctk.CTkFrame(panel, fg_color="#f8fafc", corner_radius=10)
        table_wrap.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        cols = ("id", "version", "updated", "status", "product", "category", "supplier", "owner")
        self.history_tree = ttk.Treeview(table_wrap, columns=cols, show="headings", height=9)
        headers = {
            "id": "ID",
            "version": "Versao",
            "updated": "Atualizado",
            "status": "Status",
            "product": "Produto",
            "category": "Categoria",
            "supplier": "Fornecedor",
            "owner": "Usuario",
        }
        for key, title in headers.items():
            self.history_tree.heading(key, text=title)

        self.history_tree.column("id", width=70, anchor="center")
        self.history_tree.column("version", width=70, anchor="center")
        self.history_tree.column("updated", width=160, anchor="center")
        self.history_tree.column("status", width=95, anchor="center")
        self.history_tree.column("product", width=230, anchor="w")
        self.history_tree.column("category", width=120, anchor="w")
        self.history_tree.column("supplier", width=220, anchor="w")
        self.history_tree.column("owner", width=110, anchor="w")

        scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scroll.set)

        self.history_tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)

        self._style_treeview()
        self.history_tree.bind("<Double-1>", self._on_history_double_click)

    def _style_treeview(self):
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=25, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _bind_events(self):
        vars_to_watch = [
            self.compra_liquida_var,
            self.ipi_var,
            self.st_var,
            self.icms_compra_var,
            self.pis_compra_var,
            self.cofins_compra_var,
            self.credita_icms_var,
            self.credita_pis_var,
            self.credita_cofins_var,
            self.pis_venda_var,
            self.cofins_venda_var,
            self.icms_venda_var,
            self.acrescimo_percentual_var,
            self.aplica_acrescimo_var,
        ]
        for var in vars_to_watch:
            var.trace_add("write", lambda *_: self.recalculate_all())

        self.aplica_acrescimo_var.trace_add("write", lambda *_: self._sync_markup_state())
        self.margem_cld_var.trace_add("write", lambda *_: self._on_margin_change())
        self.preco_venda_var.trace_add("write", lambda *_: self._on_price_change())

        self.bind_all("<Control-s>", lambda _e: self.save_quote())
        self.bind_all("<Control-n>", lambda _e: self.new_quote())
        self.bind_all("<F5>", lambda _e: self.refresh_history())

    def _load_defaults(self):
        self.status_var.set("RASCUNHO")

    @staticmethod
    def _currency(value: Decimal) -> str:
        text = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {text}"

    @staticmethod
    def _pct(value: Decimal) -> str:
        return f"{value:.2f}%".replace(".", ",")

    def _format_money_var(self, var: ctk.StringVar):
        if self._suspend_auto_updates:
            return
        self._suspend_auto_updates = True
        try:
            var.set(f"{parse_decimal(var.get()):.2f}")
        finally:
            self._suspend_auto_updates = False
        self.recalculate_all()

    def _format_percent_var(self, var: ctk.StringVar):
        if self._suspend_auto_updates:
            return
        self._suspend_auto_updates = True
        try:
            var.set(f"{parse_decimal(var.get()):.2f}")
        finally:
            self._suspend_auto_updates = False
        self.recalculate_all()

    def _set_calc_status(self, text: str, is_error: bool = False):
        color = "#b91c1c" if is_error else "#64748b"
        self.calc_status_label.configure(text=text, text_color=color)

    def _sync_markup_state(self):
        if bool(self.aplica_acrescimo_var.get()):
            self.acrescimo_entry.configure(state="normal")
        else:
            self.acrescimo_entry.configure(state="disabled")

    def _collect_purchase_input(self) -> PurchaseInput:
        return PurchaseInput(
            base_price=parse_decimal(self.compra_liquida_var.get()),
            ipi_rate_pct=parse_decimal(self.ipi_var.get()),
            st_rate_pct=parse_decimal(self.st_var.get()),
            icms_rate_pct=parse_decimal(self.icms_compra_var.get()),
            pis_rate_pct=parse_decimal(self.pis_compra_var.get()),
            cofins_rate_pct=parse_decimal(self.cofins_compra_var.get()),
            credit_icms=bool(self.credita_icms_var.get()),
            credit_pis=bool(self.credita_pis_var.get()),
            credit_cofins=bool(self.credita_cofins_var.get()),
        )

    def _collect_sale_input(self) -> SaleInput:
        return SaleInput(
            pis_rate_pct=parse_decimal(self.pis_venda_var.get()),
            cofins_rate_pct=parse_decimal(self.cofins_venda_var.get()),
            icms_rate_pct=parse_decimal(self.icms_venda_var.get()),
            markup_rate_pct=parse_decimal(self.acrescimo_percentual_var.get()),
            apply_markup=bool(self.aplica_acrescimo_var.get()),
        )

    def _render_result(self, result):
        self.last_result = result
        margem_liquida_venda = Decimal("0")
        if result.sale_price > Decimal("0"):
            margem_liquida_venda = (result.net_profit / result.sale_price) * Decimal("100")

        self.valor_impostos_compra_label.configure(
            text=f"Impostos Totais na Compra: {self._currency(result.purchase_taxes_total)}"
        )
        self.creditos_compra_label.configure(
            text=f"Creditos Tributarios na Compra: {self._currency(result.purchase_credits_total)}"
        )
        self.custo_efetivo_label.configure(
            text=f"Custo Efetivo (base para venda): {self._currency(result.effective_cost)}"
        )

        self.impostos_venda_label.configure(text=f"Impostos de Venda (R$): {self._currency(result.sale_taxes_value)}")
        self.lucro_liquido_label.configure(text=f"Lucro Liquido na Venda: {self._currency(result.net_profit)}")
        self.margem_cld_result_label.configure(text=f"Margem CLD Calculada: {self._pct(result.margin_pct)}")
        self.margem_liquida_venda_label.configure(
            text=f"Margem Liquida na Venda: {self._pct(margem_liquida_venda)}"
        )
        self.acrescimo_valor_label.configure(
            text=f"Acrescimo sobre venda: {self._currency(result.markup_value)} ({self._pct(result.markup_rate_pct)})"
        )
        self.margem_real_label.configure(text=f"Margem Real: {self._pct(result.real_margin_pct)}")

        self.kpi_preco.configure(text=f"Preco Final\n{self._currency(result.sale_price)}")
        self.kpi_lucro.configure(text=f"Lucro Liquido\n{self._currency(result.net_profit)}")
        self.kpi_margem.configure(text=f"Margem Liquida\n{self._pct(margem_liquida_venda)}")

        self._set_calc_status("Calculo atualizado")

    def calculate_price_from_margin(self, show_errors: bool):
        try:
            purchase = self._collect_purchase_input()
            sale = self._collect_sale_input()
            margin_pct = parse_decimal(self.margem_cld_var.get())

            result = self.service.calculate_from_margin(purchase, sale, margin_pct)

            self._updating_from_margin = True
            self.preco_venda_var.set(f"{result.sale_price:.2f}")
            self._updating_from_margin = False

            self._render_result(result)
        except Exception as exc:
            self._updating_from_margin = False
            self._set_calc_status("Falha no calculo pela margem", is_error=True)
            if show_errors:
                messagebox.showerror("Erro de calculo", str(exc))

    def calculate_margin_from_price(self, show_errors: bool):
        try:
            purchase = self._collect_purchase_input()
            sale = self._collect_sale_input()
            sale_price = parse_decimal(self.preco_venda_var.get())

            result = self.service.calculate_from_price(purchase, sale, sale_price)

            self._updating_from_price = True
            self.margem_cld_var.set(f"{result.margin_pct:.2f}")
            self._updating_from_price = False

            self._render_result(result)
        except Exception as exc:
            self._updating_from_price = False
            self._set_calc_status("Falha no calculo pelo preco", is_error=True)
            if show_errors:
                messagebox.showerror("Erro de calculo", str(exc))

    def _on_margin_change(self):
        if self._suspend_auto_updates or self._updating_from_price:
            return
        self.last_driver = "margin"
        self.calculate_price_from_margin(show_errors=False)

    def _on_price_change(self):
        if self._suspend_auto_updates or self._updating_from_margin:
            return
        self.last_driver = "price"
        self.calculate_margin_from_price(show_errors=False)

    def recalculate_all(self):
        if self._suspend_auto_updates:
            return
        if self.last_driver == "price":
            self.calculate_margin_from_price(show_errors=False)
        else:
            self.calculate_price_from_margin(show_errors=False)

    def _set_quote_info(self):
        if self.current_quote_id is None:
            self.quote_info_label.configure(text="Cotacao: Nova")
            return
        self.quote_info_label.configure(
            text=f"Cotacao: #{self.current_quote_id} | Versao: {self.current_quote_version}"
        )

    def save_quote(self):
        if self.last_result is None:
            self.recalculate_all()
        if self.last_result is None:
            messagebox.showerror("Erro", "Nao foi possivel calcular os valores antes de salvar.")
            return

        quote = QuoteRecord(
            quote_id=self.current_quote_id,
            version=self.current_quote_version,
            status=self.status_var.get().strip() or "RASCUNHO",
            product_name=self.product_var.get().strip() or "Sem produto",
            category_name=self.category_var.get().strip() or "",
            supplier_name=self.supplier_var.get().strip() or "Sem fornecedor",
            owner_user="admin",
            notes="",
            purchase=self._collect_purchase_input(),
            sale=self._collect_sale_input(),
            result=self.last_result,
        )

        try:
            saved = self.service.save_quote(quote)
        except Exception as exc:
            messagebox.showerror("Erro ao salvar", str(exc))
            return

        self.current_quote_id = saved.quote_id
        self.current_quote_version = saved.version
        self.status_var.set(saved.status)
        self._set_quote_info()
        self.refresh_history()
        messagebox.showinfo("Sucesso", "Cotacao salva com sucesso.")

    def new_quote(self):
        self._suspend_auto_updates = True
        try:
            self.current_quote_id = None
            self.current_quote_version = 1
            self.product_var.set("")
            self.category_var.set("")
            self.supplier_var.set("")
            self.status_var.set("RASCUNHO")

            self.compra_liquida_var.set("100.00")
            self.ipi_var.set("5.00")
            self.st_var.set("8.00")
            self.icms_compra_var.set("18.00")
            self.pis_compra_var.set("1.65")
            self.cofins_compra_var.set("7.60")

            self.credita_icms_var.set(1)
            self.credita_pis_var.set(1)
            self.credita_cofins_var.set(1)

            self.pis_venda_var.set("1.65")
            self.cofins_venda_var.set("7.60")
            self.icms_venda_var.set("18.00")
            self.aplica_acrescimo_var.set(0)
            self.acrescimo_percentual_var.set("0.00")
            self.margem_cld_var.set("25.00")
            self.preco_venda_var.set("0.00")
        finally:
            self._suspend_auto_updates = False

        self.last_driver = "margin"
        self.recalculate_all()
        self._set_quote_info()

    def refresh_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for row in self.service.list_recent_quotes(limit=300):
            updated = row["updated_at"].replace("T", " ")[:19]
            self.history_tree.insert(
                "",
                "end",
                iid=row["id"],
                values=(
                    row["id"],
                    row["version"],
                    updated,
                    row["status"],
                    row["product_name"],
                    row.get("category_name", ""),
                    row["supplier_name"],
                    row.get("owner_user", "admin"),
                ),
            )

    def _on_history_double_click(self, _event):
        selected = self.history_tree.focus()
        if not selected:
            return

        quote_id = int(selected)
        try:
            quote = self.service.get_quote(quote_id)
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))
            return

        self._suspend_auto_updates = True
        try:
            self.current_quote_id = quote.quote_id
            self.current_quote_version = quote.version

            self.status_var.set(quote.status)
            self.product_var.set(quote.product_name)
            self.category_var.set(quote.category_name)
            self.supplier_var.set(quote.supplier_name)

            self.compra_liquida_var.set(f"{quote.purchase.base_price:.2f}")
            self.ipi_var.set(f"{quote.purchase.ipi_rate_pct:.2f}")
            self.st_var.set(f"{quote.purchase.st_rate_pct:.2f}")
            self.icms_compra_var.set(f"{quote.purchase.icms_rate_pct:.2f}")
            self.pis_compra_var.set(f"{quote.purchase.pis_rate_pct:.2f}")
            self.cofins_compra_var.set(f"{quote.purchase.cofins_rate_pct:.2f}")

            self.credita_icms_var.set(1 if quote.purchase.credit_icms else 0)
            self.credita_pis_var.set(1 if quote.purchase.credit_pis else 0)
            self.credita_cofins_var.set(1 if quote.purchase.credit_cofins else 0)

            self.pis_venda_var.set(f"{quote.sale.pis_rate_pct:.2f}")
            self.cofins_venda_var.set(f"{quote.sale.cofins_rate_pct:.2f}")
            self.icms_venda_var.set(f"{quote.sale.icms_rate_pct:.2f}")
            self.aplica_acrescimo_var.set(1 if quote.sale.apply_markup else 0)
            self.acrescimo_percentual_var.set(f"{quote.sale.markup_rate_pct:.2f}")
            self.margem_cld_var.set(f"{quote.result.margin_pct:.2f}")
            self.preco_venda_var.set(f"{quote.result.sale_price:.2f}")
        finally:
            self._suspend_auto_updates = False

        self.last_driver = "margin"
        self._render_result(quote.result)
        self._set_quote_info()


def main():
    app = PricingERPApp()
    app.mainloop()


if __name__ == "__main__":
    main()
