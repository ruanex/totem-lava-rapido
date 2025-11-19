# 🚀 TOTEM LAVA RÁPIDO SELF-SERVICE (Gerenciamento de Kiosk Web)

[![Status](https://img.shields.io/badge/Status-Online-brightgreen)](http://lorcanaru.pythonanywhere.com)
[![Feito com](https://img.shields.io/badge/Feito%20com-Flask-blueviolet)](https://flask.palletsprojects.com/)

## 🎯 Sobre o Projeto

Este é um protótipo de sistema de ponto de venda (POS) e gestão de fluxo de usuários desenvolvido em **Python** e **Flask**. Ele simula o painel de um totem de autoatendimento para um lava-rápido, permitindo ao usuário selecionar pacotes e efetuar pagamentos, enquanto o administrador monitora as vendas em um Dashboard protegido por senha.

## ✨ Funcionalidades Principais

* **Fluxo UX Completo:** Navegação por 6 telas (Boas-vindas, Seleção, Baia, Pagamento, Confirmação, Recibo).
* **Estrutura de Pacotes:** Sistema de preços dinâmicos por tempo (10, 20, 30 min) e tipo de serviço (Básico, Completo).
* [cite_start]**Automação IoT (Simulação):** Lógica de hardware preparada para ativar relés específicos (Lavadora, Aspirador, Ar Comprimido) após a confirmação do pagamento[cite: 22, 23, 24, 25].
* **Segurança:** Área Admin (`/admin`) protegida por login e senha (`admin123`).
* [cite_start]**Dashboard Gerencial:** Exibição de faturamento total e gráfico de vendas (Chart.js)[cite: 16].
* **Pagamento Dinâmico:** Geração de QR Code (simulando PIX) na tela.
* **Persistência de Dados:** Uso de SQLite para salvar o histórico de vendas.

## ⚙️ Como Rodar Localmente (Setup)

### Pré-requisitos
* Python 3.8+
* Git

### 1. Clonar o Repositório
```bash
git clone [https://github.com/ruanex/totem-lava-rapido.git](https://github.com/ruanex/totem-lava-rapido.git)
cd totem-lava-rapido