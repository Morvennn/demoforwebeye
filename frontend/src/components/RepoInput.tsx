// Daniel Design
import { useState, type FormEvent } from "react";

interface Props {
  onSubmit: (url: string) => void;
  disabled?: boolean;
}

const EXAMPLES = [
  "https://github.com/facebook/react",
  "https://github.com/sindresorhus/awesome-nodejs",
  "https://github.com/fastapi/fastapi",
];

export function RepoInput({ onSubmit, disabled }: Props) {
  const [url, setUrl] = useState("");

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (trimmed) onSubmit(trimmed);
  };

  return (
    <form className="repo-input" onSubmit={submit}>
      <input
        type="text"
        placeholder="粘贴公开的 GitHub 仓库 URL，例如 https://github.com/owner/repo"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={disabled}
        autoFocus
      />
      <button type="submit" disabled={disabled || !url.trim()}>
        {disabled ? "分析中…" : "开始体检"}
      </button>
      <div className="examples">
        <span>试试：</span>
        {EXAMPLES.map((ex) => (
          <button
            type="button"
            key={ex}
            className="example-chip"
            disabled={disabled}
            onClick={() => {
              setUrl(ex);
              onSubmit(ex);
            }}
          >
            {ex.replace("https://github.com/", "")}
          </button>
        ))}
      </div>
    </form>
  );
}
