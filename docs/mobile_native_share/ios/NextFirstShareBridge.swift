import UIKit

/*
Purpose:
- Receive a structured NextFirst share payload and open iOS native share sheet.

Input/Output:
- Input: SharePayload(title, body, optional url, optional imageRef).
- Output: UIActivityViewController presentation with best-effort items.

Debugging:
- Validate image loading path first (file:// or https://).
- If a target app ignores subject/caption, text is still in activity items.
*/

struct SharePayload: Decodable {
    let title: String
    let body: String
    let url: String?
    let imageRef: String?

    enum CodingKeys: String, CodingKey {
        case title
        case body
        case url
        case imageRef = "image_ref"
    }
}

final class NextFirstShareBridge {
    func share(payload: SharePayload, from presenter: UIViewController) {
        var items: [Any] = []
        if !payload.body.isEmpty {
            items.append(payload.body)
        }
        if let urlString = payload.url, let url = URL(string: urlString) {
            items.append(url)
        }
        if let imageRef = payload.imageRef, let image = loadImage(ref: imageRef) {
            items.append(image)
        }

        if items.isEmpty {
            items.append(payload.title)
        }

        let activityVC = UIActivityViewController(activityItems: items, applicationActivities: nil)
        activityVC.setValue(payload.title, forKey: "subject")
        activityVC.popoverPresentationController?.sourceView = presenter.view
        presenter.present(activityVC, animated: true)
    }

    private func loadImage(ref: String) -> UIImage? {
        if ref.hasPrefix("file://"), let fileURL = URL(string: ref) {
            return UIImage(contentsOfFile: fileURL.path)
        }
        if ref.hasPrefix("/") {
            return UIImage(contentsOfFile: ref)
        }
        if ref.hasPrefix("http://") || ref.hasPrefix("https://"),
           let remoteURL = URL(string: ref),
           let data = try? Data(contentsOf: remoteURL) {
            return UIImage(data: data)
        }
        return nil
    }
}
