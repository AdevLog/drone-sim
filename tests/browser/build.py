# 產生測試頁：把 index.html 的 three.js CDN 換成本機替身（測試環境不需要網路，也不畫 3D）
import os
here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, '..', '..', 'index.html'), encoding='utf8').read()
open(os.path.join(here, 'inline.js'), 'w', encoding='utf8').write(src.split('<script>')[1].split('</script>')[0])
out = src.replace('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js', 'three/three.min.js')
open(os.path.join(here, 'test.html'), 'w', encoding='utf8').write(out)
