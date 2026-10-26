import products from "../../../../../data/fixtures/products.json";
import { Hero } from "./Hero";
import { ProductCard } from "./ProductCard";
import "./shop.css";

export function ShopPage() {
  return (
    <>
      <Hero />
      <section className="products-section" id="essentials">
        <div className="section-heading">
          <div>
            <p className="eyebrow">LESS, BUT BETTER</p>
            <h2>Ready when you are.</h2>
          </div>
          <span>Three essentials. Endless possibilities.</span>
        </div>
        <div className="product-grid">
          {products.map((product, index) => (
            <ProductCard key={product.id} product={product} index={index} />
          ))}
        </div>
      </section>
      <section className="help-strip">
        <div>
          <span className="small-mountain">△</span>
          <div>
            <h2>A question before your next adventure?</h2>
            <p>
              Find the details on shipping, returns, and looking after your
              gear.
            </p>
          </div>
        </div>
        <a className="text-link" href="#help">
          Visit the help center <span>↗</span>
        </a>
      </section>
    </>
  );
}
