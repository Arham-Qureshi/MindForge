import { Component, type ReactNode } from "react";

type Props = { children: ReactNode; fallback?: ReactNode };
type State = { hasError: boolean; msg?: string };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };
  static getDerivedStateFromError(err: unknown): State {
    return { hasError: true, msg: err instanceof Error ? err.message : String(err) };
  }
  componentDidCatch(err: unknown) {
    console.error("ViewSwitcher error", err);
  }
  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="mx-auto max-w-2xl rounded-2xl border-2 border-marker-red bg-marker-red/10 p-8 text-center">
            <p className="font-haas-grot-disp font-bold text-ink-black">Something went wrong rendering this view.</p>
            <p className="font-martian-mono text-xs text-ink-black/60 mt-2">{this.state.msg}</p>
            <p className="font-haas-grot-text text-sm mt-3">Try uploading another file or switch mode.</p>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
