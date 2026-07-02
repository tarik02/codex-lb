import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AccountSummary } from "@/features/accounts/schemas";

export type OpenAICompatibleAccountDialogPayload = {
  name: string;
  baseUrl: string;
  modelPrefix?: string | null;
  apiKey?: string;
};

export type OpenAICompatibleAccountDialogProps = {
  open: boolean;
  busy: boolean;
  error: string | null;
  account?: AccountSummary | null;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: OpenAICompatibleAccountDialogPayload) => Promise<void>;
};

export function OpenAICompatibleAccountDialog({
  open,
  busy,
  error,
  account = null,
  onOpenChange,
  onSubmit,
}: OpenAICompatibleAccountDialogProps) {
  const [name, setName] = useState("Codex-compatible API");
  const [baseUrl, setBaseUrl] = useState("https://api.openai.com");
  const [modelPrefix, setModelPrefix] = useState("");
  const [apiKey, setApiKey] = useState("");
  const isEditing = account !== null;

  useEffect(() => {
    if (!open) {
      return;
    }
    setName(account?.alias || account?.email || "Codex-compatible API");
    setBaseUrl(account?.providerBaseUrl || "https://api.openai.com");
    setModelPrefix(account?.providerModelPrefix ?? "");
    setApiKey("");
  }, [account, open]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedApiKey = apiKey.trim();
    const trimmedModelPrefix = modelPrefix.trim();
    await onSubmit({
      name,
      baseUrl,
      ...(trimmedModelPrefix ? { modelPrefix: trimmedModelPrefix } : isEditing ? { modelPrefix: null } : {}),
      ...(trimmedApiKey ? { apiKey: trimmedApiKey } : {}),
    });
    onOpenChange(false);
    setApiKey("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Codex-compatible API" : "Codex-compatible API"}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update the provider root URL, API key, or model namespace."
              : "Add an account backed by a provider root URL and API key."}
          </DialogDescription>
        </DialogHeader>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="openai-compatible-name">Name</Label>
            <Input
              id="openai-compatible-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="openai-compatible-base-url">Provider root URL</Label>
            <Input
              id="openai-compatible-base-url"
              value={baseUrl}
              onChange={(event) => setBaseUrl(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="openai-compatible-model-prefix">Model prefix</Label>
            <Input
              id="openai-compatible-model-prefix"
              value={modelPrefix}
              onChange={(event) => setModelPrefix(event.target.value)}
              placeholder="Optional"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="openai-compatible-api-key">API key</Label>
            <Input
              id="openai-compatible-api-key"
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder={isEditing ? "Leave blank to keep current key" : undefined}
            />
          </div>
          {error ? (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 px-2 py-1 text-xs text-destructive">
              {error}
            </p>
          ) : null}

          <DialogFooter>
            <Button
              type="submit"
              disabled={busy || !name.trim() || !baseUrl.trim() || (!isEditing && !apiKey.trim())}
            >
              {isEditing ? "Save changes" : "Add account"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
