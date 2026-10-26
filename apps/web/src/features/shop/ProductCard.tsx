import type products from "../../../../../data/fixtures/products.json";
import { ProductArt } from "./ProductArt";

type Product = (typeof products)[number];

export function ProductCard({
  product,
  index,
}: {
  product: Product;
  index: number;
}) {
  return (
    <article className="product-card">
      <div className={"product-image product-image-" + index}>
        <span className="product-index">0{index + 1} / THE ESSENTIALS</span>
        <ProductArt kind={product.kind} color={product.color} />
      </div>
      <div className="product-meta">
        <div>
          <p>{product.category}</p>
          <h3>{product.name}</h3>
        </div>
        <span>€{product.price}</span>
      </div>
      <p className="product-description">{product.description}</p>
      <details>
        <summary>
          Product details <span>+</span>
        </summary>
        <ul>
          {product.details.map((detail) => (
            <li key={detail}>{detail}</li>
          ))}
        </ul>
      </details>
    </article>
  );
}
