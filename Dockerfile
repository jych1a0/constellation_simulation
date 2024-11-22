FROM woodywang338/agentlayer_env:latest

WORKDIR /constellation_simulation

COPY . /constellation_simulation

RUN chmod +x /constellation_simulation/entrypoint.sh

EXPOSE 30302

ENTRYPOINT ["/constellation_simulation/entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]