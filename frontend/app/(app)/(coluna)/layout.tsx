/** Páginas de leitura e formulário: coluna de até 720px, para as linhas não ficarem longas. */
export default function ColunaLayout({ children }: LayoutProps<"/">) {
  return <div className="mx-auto w-full max-w-180">{children}</div>
}
