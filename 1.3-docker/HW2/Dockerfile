FROM python:3.10

WORKDIR /stocks_products

COPY stocks_products/ .

RUN pip install -r requirements.txt

ENV SECRET_KEY nw^y+m^wmxza1asgk+)!ua2qx9)g+#v=6%76-9i8i(6eqiw94j

RUN python3 manage.py collectstatic --no-input && python3 manage.py migrate

CMD gunicorn stocks_products.wsgi -b 0.0.0.0:8000
