"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Controller, useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { toast } from "sonner"
import { z } from "zod"

import { AvisoUsoAdmin } from "@/components/forms/aviso-uso-admin"
import { BotaoEnviar } from "@/components/forms/botao-enviar"
import { Campo } from "@/components/forms/campo"
import { CampoTipoRenda } from "@/components/forms/campo-tipo-renda"
import { ErroForm } from "@/components/forms/erro-form"
import { FieldGroup } from "@/components/ui/field"
import { editarMe } from "@/lib/api/auth"
import type { Usuario } from "@/lib/api/types"
import { formatarTelefone, mascararTelefone } from "@/lib/format"
import { aplicarErroApi, regras } from "@/lib/forms"

const esquema = z.object({
  nome: regras.obrigatorio(120),
  telefone: regras.telefone,
  cargo: regras.obrigatorio(80),
  data_nascimento: regras.dataOpcional,
  tipo_renda: z.enum(["clt", "prestador", "clt_prestador"]),
})

type Valores = z.infer<typeof esquema>

export function FormPerfil({ usuario }: { usuario: Usuario }) {
  const router = useRouter()
  const [erroGeral, setErroGeral] = useState<string | null>(null)
  const form = useForm<Valores>({
    resolver: zodResolver(esquema),
    defaultValues: {
      nome: usuario.nome,
      telefone: formatarTelefone(usuario.telefone),
      cargo: usuario.cargo,
      data_nascimento: usuario.data_nascimento ?? "",
      tipo_renda: usuario.tipo_renda,
    },
  })
  const { errors, isSubmitting, isDirty } = form.formState
  const telefone = form.register("telefone")

  async function enviar(valores: Valores) {
    setErroGeral(null)
    try {
      const atualizado = await editarMe({
        ...valores,
        data_nascimento: valores.data_nascimento || null,
      })
      form.reset({
        nome: atualizado.nome,
        telefone: formatarTelefone(atualizado.telefone),
        cargo: atualizado.cargo,
        data_nascimento: atualizado.data_nascimento ?? "",
        tipo_renda: atualizado.tipo_renda,
      })
      toast.success("Perfil salvo.")
      router.refresh()
    } catch (erro) {
      // A troca de tipo de renda pode ser recusada; a mensagem da API diz o que ajustar antes.
      setErroGeral(
        aplicarErroApi(form, erro, {
          servicos_pendentes: "tipo_renda",
          salario_invalido: "tipo_renda",
          lancamentos_sem_ciclo: "tipo_renda",
        })
      )
    }
  }

  return (
    <form onSubmit={form.handleSubmit(enviar)} noValidate>
      <FieldGroup>
        <Campo
          label="E-mail"
          type="email"
          value={usuario.email}
          readOnly
          disabled
          descricao="O e-mail não pode ser alterado."
        />
        <Campo label="Nome" autoComplete="name" erro={errors.nome?.message} {...form.register("nome")} />
        <div className="grid gap-5 sm:grid-cols-2">
          <Campo
            label="Telefone"
            type="tel"
            autoComplete="tel-national"
            inputMode="numeric"
            erro={errors.telefone?.message}
            {...telefone}
            onChange={(e) => {
              e.target.value = mascararTelefone(e.target.value)
              return telefone.onChange(e)
            }}
          />
          <Campo
            label="Data de nascimento"
            type="date"
            autoComplete="bday"
            descricao="Opcional. Apague para remover."
            erro={errors.data_nascimento?.message}
            {...form.register("data_nascimento")}
          />
        </div>
        <Campo
          label="Cargo"
          autoComplete="organization-title"
          erro={errors.cargo?.message}
          {...form.register("cargo")}
        />
        <Controller
          control={form.control}
          name="tipo_renda"
          render={({ field }) => (
            <CampoTipoRenda
              name={field.name}
              ref={field.ref}
              value={field.value}
              onBlur={field.onBlur}
              onChange={field.onChange}
              erro={errors.tipo_renda?.message}
            />
          )}
        />
        <AvisoUsoAdmin />
        <ErroForm mensagem={erroGeral} />
        <div>
          <BotaoEnviar enviando={isSubmitting} disabled={!isDirty}>
            Salvar perfil
          </BotaoEnviar>
        </div>
      </FieldGroup>
    </form>
  )
}
