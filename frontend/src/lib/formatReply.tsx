import { Fragment, type ReactNode } from "react";

const BULLET_LINE = /^\s*(?:[-*]|\d+[).])\s+(.*)/;

/** Turns the agent's plain-text reply into React nodes: lines that look like
 * a bullet ("- ", "* ") or numbered ("1)", "2.") list become an actual <ul>,
 * everything else becomes paragraphs. Mirrors app.py's format_agent_reply -
 * React already escapes text content, so no manual escaping is needed here. */
export function formatReply(text: string): ReactNode {
  const blocks: ReactNode[] = [];
  let listItems: string[] = [];
  let paragraphLines: string[] = [];

  const flushList = () => {
    if (listItems.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`}>
          {listItems.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  const flushParagraph = () => {
    if (paragraphLines.length) {
      blocks.push(
        <p key={`p-${blocks.length}`}>
          {paragraphLines.map((line, i) => (
            <Fragment key={i}>
              {i > 0 && <br />}
              {line}
            </Fragment>
          ))}
        </p>
      );
      paragraphLines = [];
    }
  };

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      flushList();
      flushParagraph();
      continue;
    }

    const match = BULLET_LINE.exec(line);
    if (match) {
      flushParagraph();
      listItems.push(match[1]);
    } else {
      flushList();
      paragraphLines.push(line);
    }
  }

  flushList();
  flushParagraph();
  return <>{blocks}</>;
}
