import customtkinter as ctk
from tkinter import messagebox

# Define o visual "dark" (escuro) e o tema "blue" (azul)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# --- Configuração dos Serviços e Preços ---
# (Nome do Serviço, Preço por MINUTO)
SERVICOS = {
    "Aspirador": 1.00,
    "Lava-Tapetes": 2.50,
    "Compressor de Ar": 0.50,
    "Box de Lavagem (Ficha)": 5.00  # Preço por ficha/unidade
}

# Opções de tempo/quantidade que o cliente pode comprar
OPCOES_TEMPO = [
    "5 minutos",
    "10 minutos",
    "15 minutos",
    "1 Ficha"  # Para o box
]


class TotemApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Totem de Pagamento Self-Service")
        self.geometry("800x500")

        self.cart = []  # Nosso "carrinho"
        self.total_price = 0.0

        # --- Layout Principal (2 colunas) ---
        self.grid_columnconfigure(0, weight=1)  # Coluna de serviços
        self.grid_columnconfigure(1, weight=1)  # Coluna do carrinho
        self.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda: Serviços ---
        self.frame_servicos = ctk.CTkFrame(self, width=380)
        self.frame_servicos.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.lbl_titulo_servicos = ctk.CTkLabel(self.frame_servicos, text="1. Adicione os Serviços",
                                                font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_titulo_servicos.pack(pady=15)

        # Criar os widgets de serviço dinamicamente
        for nome, preco in SERVICOS.items():
            # Um frame para cada item de serviço
            item_frame = ctk.CTkFrame(self.frame_servicos, fg_color="gray14")
            item_frame.pack(fill="x", padx=15, pady=10)

            label_texto = f"{nome}\n(R$ {preco:.2f}/min ou ficha)"
            label = ctk.CTkLabel(item_frame, text=label_texto, font=ctk.CTkFont(size=14))
            label.pack(pady=10)

            # Dropdown para escolher o tempo/qtde
            dropdown = ctk.CTkOptionMenu(item_frame, values=OPCOES_TEMPO, width=150)
            dropdown.pack(pady=5)

            # Botão Adicionar
            # Usamos 'lambda' para passar os argumentos corretos no momento do clique
            btn = ctk.CTkButton(item_frame, text="Adicionar",
                                command=lambda n=nome, p=preco, d=dropdown: self.adicionar_ao_carrinho(n, p, d))
            btn.pack(pady=10)

        # --- Coluna da Direita: Carrinho ---
        self.frame_carrinho = ctk.CTkFrame(self, width=380)
        self.frame_carrinho.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.lbl_titulo_carrinho = ctk.CTkLabel(self.frame_carrinho, text="2. Seu Carrinho",
                                                font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_titulo_carrinho.pack(pady=15)

        # Caixa de texto para mostrar os itens (desabilitada para edição)
        self.txt_carrinho = ctk.CTkTextbox(self.frame_carrinho, height=200, width=300)
        self.txt_carrinho.pack(pady=10)
        self.txt_carrinho.configure(state="disabled")  # Bloqueia digitação

        # Label do Preço Total
        self.lbl_total = ctk.CTkLabel(self.frame_carrinho, text="TOTAL: R$ 0.00",
                                      font=ctk.CTkFont(size=22, weight="bold"), text_color="cyan")
        self.lbl_total.pack(pady=20)

        # Botão de Pagamento
        self.btn_pagar = ctk.CTkButton(self.frame_carrinho, text="Finalizar Pagamento",
                                       command=self.realizar_pagamento,
                                       height=40, font=ctk.CTkFont(size=16))
        self.btn_pagar.pack(pady=10, fill="x", padx=30)

        # Botão Limpar
        self.btn_limpar = ctk.CTkButton(self.frame_carrinho, text="Limpar Carrinho",
                                        command=self.limpar_carrinho,
                                        fg_color="gray40", hover_color="gray50")
        self.btn_limpar.pack(fill="x", padx=30)

    def adicionar_ao_carrinho(self, nome, preco_minuto, dropdown):
        opcao_selecionada = dropdown.get()  # Ex: "10 minutos" ou "1 Ficha"

        # Extrai o número da string
        try:
            quantidade = int(opcao_selecionada.split(" ")[0])
        except ValueError:
            messagebox.showerror("Erro", "Opção de tempo inválida selecionada.")
            return

        # Calcula o subtotal deste item
        if "Ficha" in opcao_selecionada:
            subtotal = preco_minuto * quantidade
            descricao_item = f"{quantidade}x Ficha {nome}"
        else:
            subtotal = preco_minuto * quantidade
            descricao_item = f"{quantidade} min - {nome}"

        # Adiciona ao carrinho
        self.cart.append({"descricao": descricao_item, "preco": subtotal})
        self.total_price += subtotal

        self.atualizar_display_carrinho()

    def atualizar_display_carrinho(self):
        # Habilita a caixa de texto para poder alterá-la
        self.txt_carrinho.configure(state="normal")
        self.txt_carrinho.delete("1.0", "end")  # Limpa o conteúdo

        if not self.cart:
            self.txt_carrinho.insert("1.0", "Seu carrinho está vazio.")
        else:
            for item in self.cart:
                linha_texto = f"{item['descricao']} .... R$ {item['preco']:.2f}\n"
                self.txt_carrinho.insert("end", linha_texto)

        # Desabilita novamente
        self.txt_carrinho.configure(state="disabled")

        # Atualiza o label do total
        self.lbl_total.configure(text=f"TOTAL: R$ {self.total_price:.2f}")

    def limpar_carrinho(self):
        self.cart = []
        self.total_price = 0.0
        self.atualizar_display_carrinho()

    def realizar_pagamento(self):
        if not self.cart:
            messagebox.showwarning("Carrinho Vazio", "Adicione pelo menos um item ao carrinho antes de pagar.")
            return

        # Simulação de pagamento
        msg_pagamento = (
            f"Pagamento de R$ {self.total_price:.2f} APROVADO!\n\n"
            "O tempo foi creditado nas máquinas.\n"
            "Obrigado e volte sempre!"
        )
        messagebox.showinfo("Pagamento Concluído", msg_pagamento)

        # Limpa o carrinho para o próximo cliente
        self.limpar_carrinho()


# --- Para rodar o programa ---
if __name__ == "__main__":
    app = TotemApp()
    app.mainloop()