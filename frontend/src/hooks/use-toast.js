import { toast as sonnerToast } from "sonner"

const toast = ({ title, description, variant, ...options }) =>
  (variant === "destructive" ? sonnerToast.error : sonnerToast.success)(
    title,
    { description, ...options },
  )

const useToast = () => ({ toast })

export { useToast }
