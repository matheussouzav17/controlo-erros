-- Cole isto no Supabase: SQL Editor -> New query -> Run
create table if not exists erros_encomendas (
  id bigint generated always as identity primary key,
  data date not null,
  numero_encomenda text not null,
  operador text not null,
  hora_picking time not null,
  tipo_erro text not null check (tipo_erro in ('Troca', 'Falta', 'Excesso')),
  produto text,
  quantidade int check (quantidade > 0),
  observacao text,
  criado_em timestamptz not null default now()
);

-- Bloqueia o acesso público; o app usa a chave service_role (guardada só nos secrets).
alter table erros_encomendas enable row level security;
