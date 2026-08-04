import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeBlock from './CodeBlock';
import './MarkdownContent.css';

interface MarkdownContentProps {
  content: string;
}

const components: Components = {
  code(props) {
    const { children, className } = props;
    const match = /language-(\w+)/.exec(className || '');
    const code = String(children).replace(/\n$/, '');
    return match ? (
      <CodeBlock language={match[1]} code={code} />
    ) : (
      <code className="inline-code">{children}</code>
    );
  },
  a(props) {
    return <a {...props} target="_blank" rel="noopener noreferrer" />;
  },
};

function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}

export default MarkdownContent;
