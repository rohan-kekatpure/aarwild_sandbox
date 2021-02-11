from pathlib import Path
import numpy as np
import cv2
import matplotlib.pyplot as pl

from matplotlib import rc
rc('font', **{'family': 'sans-serif', 'sans-serif': ['Helvetica']})
rc('text', usetex=True)

def _colorvector(image):
    """
    Returns normalized median color of a 3-channel image
    """
    mu = np.mean(image, axis=(0, 1))
    std = np.std(image, axis=(0, 1))
    mu /= np.linalg.norm(mu)
    std /= np.linalg.norm(std)
    return mu, std

def colorcmp(v1, v2):
    clipped_cosine = min(np.dot(v1, v2), 0.999999)
    return -np.log(1.0 - clipped_cosine)

def _compute_image_color_vectors():
    pass

def _generate_similarities() -> None:
    textures_root = Path('texture_images')

    # distribution for dissimilar images
    sim_img_to_img = []
    sim_within_img = []

    for i, img1_path in enumerate(textures_root.glob('*')):
        img1 = cv2.imread(img1_path.as_posix())
        if img1_path.name == '.DS_Store':
            continue
        mu_img1, std_img1 = _colorvector(img1)

        # compute within image similarity
        H, W = img1.shape[:2]
        wp, hp = int(W / 2), int(H / 2)
        for _ in range(100):
            y0 = np.random.randint(0, H - hp, 1)[0]
            x0 = np.random.randint(0, W - wp, 1)[0]
            patch = img1[y0: y0 + hp, x0: x0 + wp, :]
            mu_patch, std_patch = _colorvector(patch)
            mu_sim = colorcmp(mu_patch, mu_img1)
            std_sim = colorcmp(std_patch, std_img1)
            sim_within_img.append([mu_sim, std_sim])

        for img2_path in textures_root.glob('*'):
            if img2_path.name == '.DS_Store':
                continue
            if img2_path == img1_path:
                continue
            img2 = cv2.imread(img2_path.as_posix())
            print(i, img1_path, img2_path)
            mu_img2, std_img2 = _colorvector(img2)
            mu_sim_imgs = colorcmp(mu_img2, mu_img1)
            std_sim_imgs = colorcmp(std_img2, std_img1)
            sim_img_to_img.append([mu_sim_imgs, std_sim_imgs])
    sim_img_to_img = np.array(sim_img_to_img)
    sim_within_img = np.array(sim_within_img)
    np.save('_sim_image_to_image.npy', sim_img_to_img)
    np.save('_sim_within_image.npy', sim_within_img)

def _plot2d() -> None:
    sim_img_to_img = np.load('_sim_image_to_image_2d.npy')
    sim_within_img = np.load('_sim_within_image_2d.npy')
    pl.plot(sim_within_img[:, 0], sim_within_img[:, 1], 'go', alpha=0.3, mfc='none')
    pl.plot(sim_img_to_img[:, 0], sim_img_to_img[:, 1], 'ro', alpha=0.3, mfc='none')
    pl.xlabel(r'$-\log(1 - \mu_1^T\mu_2)$')
    pl.ylabel(r'$-\log(1 - \sigma_1^T\sigma_2)$')
    pl.savefig('_similarity_distribution_2d.jpg')
    pl.show()

def _plot() -> None:
    sim_img_to_img = np.load('_sim_image_to_image_2d.npy')
    sim_within_img = np.load('_sim_within_image_2d.npy')
    from IPython import embed; embed(); exit(0)
    args = dict(histtype='step', density=True, bins=32)
    pl.hist(sim_img_to_img, color='r', **args)
    pl.hist(sim_within_img, color='g', **args)
    pl.xlabel('similarity score')
    pl.ylabel('normalized count')
    pl.xlim([0, 14])
    pl.ylim([0, 1])
    pl.savefig('_similarity_distribution_cv4.jpg')
    pl.show()

if __name__ == '__main__':
    # _generate_similarities()
    _plot2d()
