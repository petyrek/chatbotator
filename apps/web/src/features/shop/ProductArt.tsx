type Props = { kind: string; color: string };
export function ProductArt({ kind, color }: Props) {
  return (
    <svg className="product-art" viewBox="0 0 360 270" aria-hidden="true">
      <ellipse cx="180" cy="235" rx="83" ry="10" fill="#253b2e" opacity=".08" />
      {kind === "pack" && (
        <g transform="rotate(-8 180 145)">
          <path
            d="M147 71 C137 19 221 19 213 71"
            fill="none"
            stroke="#62452f"
            strokeWidth="11"
          />
          <path
            d="M126 84 Q112 126 121 206 M231 84 Q246 126 238 206"
            fill="none"
            stroke="#62452f"
            strokeWidth="14"
          />
          <rect x="121" y="63" width="116" height="167" rx="34" fill={color} />
          <path
            d="M122 101 Q177 127 236 101 L233 72 Q180 47 127 72Z"
            fill="#d1865b"
          />
          <rect x="140" y="144" width="78" height="69" rx="13" fill="#a95535" />
          <path d="M147 153 H210" stroke="#dfb08b" strokeWidth="3" />
          <path d="M145 98V135 M211 98V135" stroke="#584936" strokeWidth="7" />
          <rect x="141" y="114" width="9" height="13" rx="2" fill="#d9c39e" />
          <rect x="207" y="114" width="9" height="13" rx="2" fill="#d9c39e" />
          <path d="M169 177L180 162L191 177Z" fill="#e7d4b4" />
        </g>
      )}
      {kind === "tent" && (
        <g>
          <path d="M47 221L150 66L309 217Z" fill={color} />
          <path d="M150 66L201 222L309 217Z" fill="#8c8c5d" />
          <path d="M66 219L150 89L190 219Z" fill="#dfd8b6" />
          <path d="M104 219L150 126L174 219Z" fill="#445548" />
          <path
            d="M47 221L150 66L201 222"
            fill="none"
            stroke="#555d44"
            strokeWidth="4"
          />
          <path
            d="M150 66L30 235 M309 217L332 235"
            stroke="#8b7857"
            strokeWidth="2"
          />
          <path d="M23 235H39 M325 235H340" stroke="#535648" strokeWidth="3" />
        </g>
      )}
      {kind === "bottle" && (
        <g transform="rotate(9 180 145)">
          <path
            d="M164 46 Q157 19 181 19 Q204 19 198 46"
            fill="none"
            stroke="#354943"
            strokeWidth="5"
          />
          <rect x="157" y="37" width="48" height="31" rx="8" fill="#354943" />
          <path
            d="M157 66 Q141 80 141 100V209Q141 231 163 231H198Q220 231 220 209V100Q220 80 204 66Z"
            fill={color}
          />
          <path
            d="M153 104V199"
            stroke="#a6b9ac"
            strokeWidth="7"
            strokeLinecap="round"
            opacity=".6"
          />
          <path d="M166 163L180 141L196 163Z" fill="#e1e7d7" />
          <path d="M175 151L180 141L186 151Z" fill="#77938c" />
        </g>
      )}
    </svg>
  );
}
