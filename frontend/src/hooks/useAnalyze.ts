// Daniel Design
import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentReport,
  FinalReport,
  JudgeReport,
  RepoMeta,
} from "../types";

export type Status = "idle" | "loading" | "done" | "error";

export interface AgentState {
  text: string;
  report: AgentReport | null;
  running: boolean;
}

export interface JudgeState {
  text: string;
  report: JudgeReport | null;
  running: boolean;
}

const EMPTY_AGENT: AgentState = { text: "", report: null, running: false };
const EMPTY_JUDGE: JudgeState = { text: "", report: null, running: false };

function parse<T = unknown>(raw: string): T {
  return JSON.parse(raw) as T;
}

export function useAnalyze() {
  const [status, setStatus] = useState<Status>("idle");
  const [meta, setMeta] = useState<RepoMeta | null>(null);
  const [codeAudit, setCodeAudit] = useState<AgentState>(EMPTY_AGENT);
  const [productValue, setProductValue] = useState<AgentState>(EMPTY_AGENT);
  const [judge, setJudge] = useState<JudgeState>(EMPTY_JUDGE);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const esRef = useRef<EventSource | null>(null);
  const finishedRef = useRef(false);

  const reset = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    finishedRef.current = false;
    setStatus("idle");
    setMeta(null);
    setCodeAudit(EMPTY_AGENT);
    setProductValue(EMPTY_AGENT);
    setJudge(EMPTY_JUDGE);
    setFinalReport(null);
    setError(null);
  }, []);

  const run = useCallback(
    (url: string) => {
      reset();
      setStatus("loading");
      const es = new EventSource(`/api/analyze?repo_url=${encodeURIComponent(url)}`);
      esRef.current = es;

      const appendDelta = (agent: string, delta: string) => {
        if (agent === "code_audit") setCodeAudit((s) => ({ ...s, text: s.text + delta }));
        else if (agent === "product_value") setProductValue((s) => ({ ...s, text: s.text + delta }));
        else if (agent === "judge") setJudge((s) => ({ ...s, text: s.text + delta }));
      };
      const setRunning = (agent: string, running: boolean) => {
        if (agent === "code_audit") setCodeAudit((s) => ({ ...s, running }));
        else if (agent === "product_value") setProductValue((s) => ({ ...s, running }));
        else if (agent === "judge") setJudge((s) => ({ ...s, running }));
      };

      es.addEventListener("meta", (e) => setMeta(parse<RepoMeta>((e as MessageEvent).data)));

      es.addEventListener("agent_start", (e) => {
        const { agent } = parse<{ agent: string }>((e as MessageEvent).data);
        setRunning(agent, true);
      });

      es.addEventListener("agent_delta", (e) => {
        const { agent, delta } = parse<{ agent: string; delta: string }>((e as MessageEvent).data);
        appendDelta(agent, delta);
      });

      es.addEventListener("agent_done", (e) => {
        const { agent, report } = parse<{ agent: string; report: AgentReport }>((e as MessageEvent).data);
        if (agent === "code_audit") setCodeAudit((s) => ({ ...s, report, running: false }));
        else if (agent === "product_value") setProductValue((s) => ({ ...s, report, running: false }));
      });

      es.addEventListener("judge_done", (e) => {
        const { report } = parse<{ report: JudgeReport }>((e as MessageEvent).data);
        setJudge((s) => ({ ...s, report, running: false }));
      });

      es.addEventListener("report", (e) => {
        if (finishedRef.current) return;
        finishedRef.current = true;
        setFinalReport(parse<FinalReport>((e as MessageEvent).data));
        setStatus("done");
        es.close();
      });

      // Our server-sent `error` event AND native EventSource errors both land here.
      // Server errors carry JSON `data`; native connection errors do not.
      es.addEventListener("error", (e) => {
        if (finishedRef.current) return;
        const data = (e as MessageEvent).data;
        if (data) {
          try {
            setError(parse<{ message: string }>(data).message);
          } catch {
            setError(data);
          }
        } else {
          setError("连接中断或服务端错误，请检查后端是否运行。");
        }
        finishedRef.current = true;
        setStatus("error");
        es.close();
      });
    },
    [reset],
  );

  useEffect(() => () => esRef.current?.close(), []);

  return {
    status,
    meta,
    codeAudit,
    productValue,
    judge,
    finalReport,
    error,
    run,
    reset,
  };
}
