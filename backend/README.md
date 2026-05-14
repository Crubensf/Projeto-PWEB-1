rodar o server com 
uvicorn main:app --reload


a aplicaçao utiliza o sqlite para armazenar os dados de login com um hash na senha, a funçao de comunicaçao do backend com o front esta encapsulado no app.js. Os dados são armazenados com forma de tabela pelo sqlAlchemy, para retorno ao usuario o pydantic é utilizado para conversão dos dados utilizados