"""Foto do usuário: upload validado pelo conteúdo, arquivo em disco, troca e remoção."""

import pytest

from app.config.constants import DIR_ARQUIVOS, ROTA_ARQUIVOS, TAMANHO_MAXIMO_IMAGEM_MB
from app.utils import arquivo_utils

# Só a assinatura importa para a validação; o resto é enchimento.
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 64


def _no_disco(caminho_publico: str):
    return DIR_ARQUIVOS / caminho_publico.removeprefix(f"{ROTA_ARQUIVOS}/")


def _enviar(api, conteudo: bytes, nome="foto.jpg", tipo="image/jpeg"):
    return api.put("/conta/foto", files={"arquivo": (nome, conteudo, tipo)})


@pytest.fixture()
def logado(api):
    api.post(
        "/conta/cadastro",
        json={
            "nome": "Caio",
            "email": "caio@test.com",
            "senha": "senha1234",
            "aceite_termos": True,
        },
    )


class TestTrocarFoto:
    @pytest.mark.parametrize(
        ("conteudo", "extensao"), [(JPEG, "jpg"), (PNG, "png"), (WEBP, "webp")]
    )
    def test_aceita_jpg_png_e_webp(self, api, logado, conteudo, extensao):
        res = _enviar(api, conteudo)

        assert res.status_code == 200
        foto = res.json()["foto_url"]
        assert foto.startswith(f"{ROTA_ARQUIVOS}/fotos/")
        assert foto.endswith(f".{extensao}")
        assert _no_disco(foto).read_bytes() == conteudo

    def test_arquivo_fica_acessivel_pela_api(self, api, logado):
        foto = _enviar(api, JPEG).json()["foto_url"]

        res = api.get(foto)

        assert res.status_code == 200
        assert res.content == JPEG

    def test_extensao_do_nome_e_ignorada(self, api, logado):
        # Nome e Content-Type dizem JPEG, mas o conteúdo é PNG: vale o conteúdo.
        foto = _enviar(api, PNG, nome="foto.jpg", tipo="image/jpeg").json()["foto_url"]

        assert foto.endswith(".png")

    def test_recusa_arquivo_que_nao_e_imagem(self, api, logado):
        res = _enviar(api, b"<script>alert(1)</script>", nome="foto.jpg")

        assert res.status_code == 415

    def test_recusa_imagem_grande_demais(self, api, logado):
        grande = JPEG + b"\x00" * (TAMANHO_MAXIMO_IMAGEM_MB * 1024 * 1024)

        res = _enviar(api, grande)

        assert res.status_code == 413

    def test_recusa_arquivo_vazio(self, api, logado):
        assert _enviar(api, b"").status_code == 422

    def test_trocar_apaga_a_foto_anterior(self, api, logado):
        primeira = _enviar(api, JPEG).json()["foto_url"]

        segunda = _enviar(api, PNG).json()["foto_url"]

        assert segunda != primeira
        assert not _no_disco(primeira).exists()
        assert _no_disco(segunda).exists()

    def test_sem_login_da_401(self, api):
        assert _enviar(api, JPEG).status_code == 401


class TestRemoverFoto:
    def test_remove_do_banco_e_do_disco(self, api, logado):
        foto = _enviar(api, JPEG).json()["foto_url"]

        res = api.delete("/conta/foto")

        assert res.status_code == 200
        assert res.json()["foto_url"] is None
        assert not _no_disco(foto).exists()

    def test_sem_foto_nao_da_erro(self, api, logado):
        assert api.delete("/conta/foto").status_code == 200


class TestPatchNaoMexeNaFoto:
    def test_foto_url_no_patch_e_ignorada(self, api, logado):
        foto = _enviar(api, JPEG).json()["foto_url"]

        res = api.patch("/conta", json={"foto_url": "https://malicioso.example/x.jpg"})

        assert res.json()["foto_url"] == foto


class TestRemoverArquivo:
    def test_nao_sai_da_pasta_de_arquivos(self, tmp_path):
        fora = DIR_ARQUIVOS.parent / "nao_apagar.txt"
        fora.write_text("x")
        try:
            arquivo_utils.remover_arquivo(f"{ROTA_ARQUIVOS}/../nao_apagar.txt")
            assert fora.exists()
        finally:
            fora.unlink(missing_ok=True)

    def test_ignora_caminho_que_nao_e_nosso(self):
        arquivo_utils.remover_arquivo("https://outro-site.example/foto.jpg")  # não levanta
