"""Regressão para ângulos que atravessam 360° nas curvas de proporções."""
import unittest
import numpy as np
from proporcoes import fontes


class InterpolacaoAngular(unittest.TestCase):
    def amostrar(self, inicio, fim, valor=.5):
        curvas = {'osso': np.array([
            [0, 0, 0, 0, *inicio, 1, 1, 1],
            [1, 2, 4, 6, *fim, 3, 5, 7],
        ], dtype=float)}
        tabela = '0\tosso\t1\t1\t1\t1\t1\t1\t1\t1\t1'
        return fontes(curvas, tabela, [valor], {0: 'osso'})[0]

    def test_cruza_zero_pelo_caminho_curto(self):
        r = self.amostrar([0, 359, 350], [359, 0, 10])
        np.testing.assert_allclose(list(r['vctRot'].values()), [-.5, 359.5, 360])

    def test_posicao_e_escala_continuam_lineares(self):
        r = self.amostrar([0, 0, 0], [20, 40, 60])
        np.testing.assert_allclose(list(r['vctPos'].values()), [1, 2, 3])
        np.testing.assert_allclose(list(r['vctScl'].values()), [2, 3, 4])
        np.testing.assert_allclose(list(r['vctRot'].values()), [10, 20, 30])

    def test_valor_da_rena_na_transicao_da_saia(self):
        r = self.amostrar([0, 0, 0], [0, 0, 359.6666564941406], .227611541748047)
        self.assertAlmostEqual(r['vctRot']['z'], -.075873, places=5)


if __name__ == '__main__':
    unittest.main()
