<script lang="ts">
	import type { ReconciledComponent } from '$lib/inventory/types';

	interface Props {
		items: ReconciledComponent[];
	}

	let { items }: Props = $props();
</script>

{#if items.length}
	<ul class="component-list">
		{#each items as item (`${item.family}-${item.serialNumber}-${item.label}`)}
			<li>
				<div>
					<strong>{item.label}</strong>
					<span>{item.serialNumber}</span>
				</div>
				<em>{item.source}</em>
			</li>
		{/each}
	</ul>
{:else}
	<p class="empty">Sin componentes detectados.</p>
{/if}

<style>
	.component-list {
		list-style: none;
		margin: 0;
		padding: 0;
	}

	.component-list li {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 12px 0;
		border-top: 1px solid #253140;
	}

	.component-list strong,
	.component-list span {
		display: block;
	}

	.component-list span {
		margin-top: 4px;
		color: #9aa8b8;
		font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
		font-size: 0.82rem;
	}

	.component-list em {
		color: #81d8d0;
		font-size: 0.8rem;
		font-style: normal;
		text-transform: uppercase;
	}

	.empty {
		margin: 0;
		color: #9aa8b8;
	}
</style>
