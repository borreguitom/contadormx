"use client";
import * as Select from "@radix-ui/react-select";

type Option = { value: string; label: string };

interface SelectInputProps {
  value: string;
  onChange: (v: string) => void;
  options: Option[] | string[];
  placeholder?: string;
  className?: string;
}

function normalize(options: Option[] | string[]): Option[] {
  if (options.length === 0) return [];
  return typeof options[0] === "string"
    ? (options as string[]).map(o => ({ value: o, label: o }))
    : (options as Option[]);
}

export function SelectInput({ value, onChange, options, placeholder, className = "" }: SelectInputProps) {
  const opts = normalize(options);
  const current = opts.find(o => o.value === value);

  return (
    <Select.Root value={value} onValueChange={onChange}>
      <Select.Trigger
        className={`flex items-center justify-between w-full border border-white/10 rounded-xl px-3 py-2 text-sm text-green-50 bg-white/5 focus:outline-none focus:border-green-500/40 data-[placeholder]:text-gray-500 ${className}`}
      >
        <Select.Value placeholder={placeholder ?? "Seleccionar..."}>
          {current?.label ?? placeholder ?? "Seleccionar..."}
        </Select.Value>
        <Select.Icon>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="text-gray-400 ml-2 flex-shrink-0">
            <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          position="popper"
          sideOffset={4}
          className="z-50 min-w-[var(--radix-select-trigger-width)] overflow-hidden rounded-xl border border-white/10 bg-[#0d1a0d] shadow-xl shadow-black/40"
        >
          <Select.Viewport className="p-1">
            {opts.map(o => (
              <Select.Item
                key={o.value}
                value={o.value}
                className="relative flex items-center px-3 py-2 text-sm text-green-100 rounded-lg cursor-pointer outline-none
                  data-[highlighted]:bg-green-700/40 data-[highlighted]:text-green-50
                  data-[state=checked]:text-green-300 data-[state=checked]:font-medium"
              >
                <Select.ItemText>{o.label}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}
