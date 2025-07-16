import { useState, useEffect, useRef } from 'react'
import { FileText, Copy, Download, Eye, EyeOff, Check, Save, GitCompare } from 'lucide-react'
import type { YamlFile } from '../App'
import { cn } from '../lib/utils'
import Prism from 'prismjs'
import 'prismjs/components/prism-yaml'
import 'prismjs/themes/prism.css'
// @ts-ignore
import DiffMatchPatch from 'diff-match-patch'

interface YamlPanelProps {
  yamlFiles: YamlFile[]
  isLoading?: boolean
}

interface DiffLine {
  type: 'equal' | 'insert' | 'delete'
  text: string
}

function computeDiffLines(oldText: string, newText: string): DiffLine[] {
  const dmp = new DiffMatchPatch()
  const diff = dmp.diff_main(oldText, newText)
  dmp.diff_cleanupSemantic(diff)

  const lines: DiffLine[] = []
  diff.forEach(([op, data]: [number, string]) => {
    const split = data.split('\n')
    // Remove last empty string if data ends with \n
    if (split.length > 1 && split[split.length - 1] === '') split.pop()
    split.forEach((line: string) => {
      if (op === DiffMatchPatch.DIFF_INSERT) lines.push({ type: 'insert', text: line })
      else if (op === DiffMatchPatch.DIFF_DELETE) lines.push({ type: 'delete', text: line })
      else lines.push({ type: 'equal', text: line })
    })
  })
  return lines
}

// Function to decode escaped characters in YAML content
function decodeEscaped(content: string) {
  return content.replace(/\\n/g, '\n').replace(/\\'/g, "'").replace(/\\"/g, '"')
}

export function YamlPanel({ yamlFiles, isLoading = false }: YamlPanelProps) {
  const [activeFile, setActiveFile] = useState(0)
  const [showLineNumbers, setShowLineNumbers] = useState(true)
  const [copiedFile, setCopiedFile] = useState<string | null>(null)
  const [showDiff, setShowDiff] = useState(true)
  const prevYamlRef = useRef<{ [name: string]: string }>({})
  const lastUpdateRef = useRef<{ [name: string]: string }>({})

  // Highlight syntax when content changes
  useEffect(() => {
    Prism.highlightAll()
  }, [yamlFiles, activeFile, showDiff])

  // Always keep both files in the panel
  const allFileNames = ['agents.yaml', 'workflow.yaml']
  const filesToShow: YamlFile[] = allFileNames.map(name =>
    yamlFiles.find(f => f.name === name) || { name, content: '', language: 'yaml' as const }
  )

  // Track changes for diff - store the previous version before updating
  useEffect(() => {
    filesToShow.forEach(file => {
      const currentContent = file.content.trim()
      const lastContent = lastUpdateRef.current[file.name] || ''

      // If content changed and we had previous content, store it for diff
      if (currentContent !== lastContent && lastContent !== '') {
        prevYamlRef.current[file.name] = lastContent
      }

      // Update the last known content
      if (currentContent !== '') {
        lastUpdateRef.current[file.name] = currentContent
      }
    })
  }, [filesToShow.map(f => f.content).join('')])

  const handleCopy = async (content: string, fileName: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedFile(fileName)
      setTimeout(() => setCopiedFile(null), 2000)
    } catch (err) {
      console.error('Failed to copy: ', err)
    }
  }

  const handleDownload = (file: YamlFile) => {
    const blob = new Blob([file.content], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = file.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const renderLineNumbers = (content: string) => {
    const lines = content.split('\n')
    return (
      <div className="flex">
        <div className="w-12 flex-shrink-0 bg-gray-100 text-gray-500 text-sm font-mono p-4 border-r border-gray-200 font-['Courier_New']">
          {lines.map((_, index) => (
            <div key={index} className="text-right">
              {index + 1}
            </div>
          ))}
        </div>
        <div className="flex-1">
          <pre className="text-sm font-mono p-4 overflow-x-auto bg-white font-['Courier_New'] whitespace-pre">
            <code className="language-yaml whitespace-pre">{decodeEscaped(content)}</code>
          </pre>
        </div>
      </div>
    )
  }

  const renderDiff = (oldContent: string, newContent: string) => {
    if (oldContent === newContent || oldContent === '') {
      // No diff to show, just render the new content
      return (
        <pre className="text-sm font-mono p-4 overflow-x-auto bg-white font-['Courier_New'] whitespace-pre">
          <code className="language-yaml whitespace-pre">{decodeEscaped(newContent)}</code>
        </pre>
      )
    }

    const lines = computeDiffLines(oldContent, newContent)

    return (
      <div>
        <div className="px-4 py-2 bg-blue-50 border-b border-blue-200 text-xs text-blue-700 font-medium">
          Showing changes (green = added, red = removed)
        </div>
        <div className="text-sm font-mono px-4 py-2 overflow-y-auto h-[500px] bg-white font-['Courier_New'] whitespace-pre">
          {lines.map((line, idx) => {
            const lineStyle = line.type === 'insert'
              ? { backgroundColor: '#dcfce7', color: '#166534' } // green-100 bg, green-800 text
              : line.type === 'delete'
              ? { backgroundColor: '#fee2e2', color: '#991b1b' } // red-100 bg, red-800 text
              : { color: '#1f2937' } // gray-800 text

            return (
              <div
                key={idx}
                style={lineStyle}
                className="w-full"
              >
                {line.type === 'insert' ? '+' : line.type === 'delete' ? '-' : ' '} {decodeEscaped(line.text)}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const hasContent = filesToShow.some(file => file.content.trim() !== '')

  return (
    <div className="w-1/3 border-l border-gray-100 bg-white flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900">Generated Files</h2>
        <div className="flex items-center gap-2">
          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-blue-600">
              <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span>Updating...</span>
            </div>
          )}
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="p-2 rounded-lg hover:bg-gray-50 hover:text-gray-700 transition-colors"
            title={showDiff ? 'Show full YAML' : 'Show diff'}
          >
            <GitCompare size={18} className={showDiff ? 'text-blue-600' : ''} />
          </button>
          <button
            onClick={() => setShowLineNumbers(!showLineNumbers)}
            className="p-2 rounded-lg hover:bg-gray-50 hover:text-gray-700 transition-colors"
            title={showLineNumbers ? 'Hide line numbers' : 'Show line numbers'}
          >
            {showLineNumbers ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
      </div>

      {/* File Tabs */}
      <div className="flex border-b border-gray-100">
        {filesToShow.map((file, index) => {
          const hasFileContent = file.content.trim() !== ''
          return (
            <button
              key={file.name}
              onClick={() => setActiveFile(index)}
              className={cn(
                "flex items-center gap-2 px-6 py-4 text-xs border-b-2 transition-all duration-200 relative",
                activeFile === index
                  ? "border-blue-600 text-blue-700 bg-blue-50 font-medium"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50",
                hasFileContent && "text-green-600"
              )}
            >
              <FileText size={16} />
              <span>{file.name}</span>
              {hasFileContent && (
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              )}
            </button>
          )
        })}
      </div>

      {/* File Content */}
      <div className="flex-1 overflow-hidden">
        {filesToShow.length > 0 && hasContent ? (
          <div className="h-full flex flex-col">
            {/* File Actions */}
            <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gray-50">
              <span className="text-xs text-gray-500 font-medium">
                {filesToShow[activeFile].name}
                {filesToShow[activeFile].content.trim() !== '' && (
                  <span className="ml-2 text-green-600">• Generated</span>
                )}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleCopy(filesToShow[activeFile].content, filesToShow[activeFile].name)}
                  className={cn(
                    "p-2 rounded-lg transition-colors flex items-center gap-1",
                    copiedFile === filesToShow[activeFile].name
                      ? "bg-green-100 text-green-700"
                      : "hover:bg-white hover:text-gray-700"
                  )}
                  title="Copy to clipboard"
                >
                  {copiedFile === filesToShow[activeFile].name ? (
                    <>
                      <Check size={16} />
                      <span className="text-xs">Copied!</span>
                    </>
                  ) : (
                    <Copy size={16} />
                  )}
                </button>
                <button
                  onClick={() => handleDownload(filesToShow[activeFile])}
                  className="p-2 rounded-lg hover:bg-white hover:text-gray-700 transition-colors"
                  title="Download file"
                >
                  <Download size={16} />
                </button>
                <button
                  onClick={() => handleDownload(filesToShow[activeFile])}
                  className="p-2 rounded-lg hover:bg-white hover:text-gray-700 transition-colors"
                  title="Save file"
                >
                  <Save size={16} />
                </button>
              </div>
            </div>

            {/* YAML Content */}
            <div className="flex-1 overflow-auto">
              {filesToShow[activeFile].content.trim() === '' ? (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <div className="text-center max-w-sm">
                    <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <FileText size={24} className="text-gray-400" />
                    </div>
                    <h3 className="text-xs font-medium text-gray-900 mb-2">No content yet</h3>
                    <p className="text-xs text-gray-500">Ask the AI to generate content for this file</p>
                  </div>
                </div>
              ) : showDiff ? (
                renderDiff(prevYamlRef.current[filesToShow[activeFile].name] || '', filesToShow[activeFile].content)
              ) : showLineNumbers ? (
                renderLineNumbers(filesToShow[activeFile].content)
              ) : (
                <pre className="text-sm font-mono p-6 overflow-x-auto bg-gray-50 font-['Courier_New'] whitespace-pre">
                  <code className="language-yaml whitespace-pre">{decodeEscaped(filesToShow[activeFile].content)}</code>
                </pre>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center max-w-sm">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FileText size={24} className="text-gray-400" />
              </div>
              <h3 className="text-xs font-medium text-gray-900 mb-2">No YAML files generated yet</h3>
              <p className="text-xs text-gray-500">Start a conversation to generate files</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}