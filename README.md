# guess-word
詞義高手 - 推敲辭義，贏得勝利，提升你的國文造詣

## 安裝
1. 下載此專案
2. 建立資料庫，格式於```database.sql```
3. 至 Apache config 設定 WSGIScriptAlias 至 ```guess_word.wsgi``` 的路徑
3. 設定 ```guess_word.wsgi```
4. 複製 ```config.sample.ini``` 至 ```config.ini``` 並設定裡面的內容
5. 複製 ```zhconversion.sample.ini``` 至 ```zhconversion.ini``` 並設定裡面的內容（可從[ZhConversion.php · mediawiki](https://phabricator.wikimedia.org/source/mediawiki/browse/master/languages/data/ZhConversion.php)取得）
6. 至[《重編國語辭典修訂本》資料下載](http://resources.publicense.moe.edu.tw/dict_reviseddict_download.html)下載文字資料庫，並解壓縮後將三個 xls 檔另存為 csv 檔
7. 分別對三個 csv 檔執行```python import.py csv檔名.csv```
8. 完成
