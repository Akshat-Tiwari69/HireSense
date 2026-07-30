import { beforeEach, describe, expect, it, vi } from "vitest"
import { toast as sonnerToast } from "sonner"

import { useToast } from "./use-toast"

vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}))

describe("useToast", () => {
  beforeEach(() => vi.clearAllMocks())

  it("uses a success toast by default", () => {
    useToast().toast({ title: "Saved", description: "Done", duration: 3000 })

    expect(sonnerToast.success).toHaveBeenCalledWith("Saved", {
      description: "Done",
      duration: 3000,
    })
  })

  it("maps destructive toasts to errors", () => {
    useToast().toast({ title: "Failed", variant: "destructive" })

    expect(sonnerToast.error).toHaveBeenCalledWith("Failed", {
      description: undefined,
    })
  })
})
