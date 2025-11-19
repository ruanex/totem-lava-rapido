import qrcode

# O endereço do seu site (Link Mestre)
link_do_site = "http://lorcanaru.pythonanywhere.com"

# Criação do QR Code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H, # Alta correção de erro (permite por logo no meio se quiser)
    box_size=20, # Tamanho grande
    border=4,
)

qr.add_data(link_do_site)
qr.make(fit=True)

# Cria a imagem com cores personalizadas (Preto e Branco clássico ou colorido)
img = qr.make_image(fill_color="black", back_color="white")

# Salva o arquivo
nome_arquivo = "qr_para_poster.png"
img.save(nome_arquivo)

print(f"Sucesso! O arquivo '{nome_arquivo}' foi criado na pasta do projeto.")