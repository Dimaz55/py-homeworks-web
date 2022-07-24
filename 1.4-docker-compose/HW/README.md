## Инструкция по запуску:
1. Перейти в папку HW2:

   `cd HW2`

2. Запустить создание образа:

    `docker build -t my_api .`
3. Запустить контейнер:

    `docker run --name=my-api -d -p 8000:8000 my_api`
4. API доступен по адресу:
    
    http://127.0.0.1:8000/api/v1/products/
5. Для остановки контейнера:

    `docker stop my-api`
